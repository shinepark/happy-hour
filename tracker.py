"""
DC Happy Hour Tracker
A Python application to track and rank happy hour venues in DC
"""
import json
import os
from datetime import datetime, time
from typing import List, Dict, Optional
import re

class HappyHourVenue:

    def __init__(self, name: str, neighborhood: str, happy_hour_days: str,
                 happy_hour_times: str, rating: float, offers: str):
        self.name = name
        self.neighborhood = neighborhood
        self.happy_hour_days = happy_hour_days
        self.happy_hour_times = happy_hour_times
        self.rating = rating
        self.offers = offers

    def to_dict(self) -> Dict:
        """Convert venue to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'neighborhood': self.neighborhood,
            'happy_hour_days': self.happy_hour_days,
            'happy_hour_times': self.happy_hour_times,
            'rating': self.rating,
            'offers': self.offers
        }

    def from_dict(cls, data: Dict) -> 'HappyHourVenue':
        """Create venue from dictionary"""
        return cls(
            data['name'],
            data['neighborhood'],
            data['happy_hour_days'],
            data['happy_hour_times'],
            data['rating'],
            data['offers']
        )

    def is_open_now(self) -> bool:
        """Check if venue's happy hour is currently active"""
        now = datetime.now()
        current_day = now.weekday()  # 0 = Monday, 6 = Sunday
        current_time = now.time()

        # verify there is happy hour that day
        if not self._is_valid_day(current_day):
            return False

        # verify time is within happy hour
        start_time, end_time = self._parse_happy_hour_times()
        if start_time and end_time:
            return start_time <= current_time <= end_time

        return False

    def _is_valid_day(self, day: int) -> bool:
        """Check if given day (0=Monday) is a valid happy hour day"""
        days_str = self.happy_hour_days.lower()

        # Handle common patterns
        if 'mon-fri' in days_str or 'monday-friday' in days_str:
            return 0 <= day <= 4  # Monday to Friday
        elif 'daily' in days_str or 'every day' in days_str:
            return True
        elif 'weekend' in days_str:
            return day in [5, 6]  # Saturday, Sunday

        # individual days
        day_mapping = {
            'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6
        }

        for day_abbr, day_num in day_mapping.items():
            if day_abbr in days_str and day_num == day:
                return True

        return False

    def _parse_happy_hour_times(self) -> tuple:
        """Parse happy hour time string and return start/end times"""
        # "4:00 PM - 7:00 PM" or "4:00PM-7:00PM"
        pattern = r'(\d{1,2}):(\d{2})\s*(AM|PM)\s*-\s*(\d{1,2}):(\d{2})\s*(AM|PM)'
        match = re.search(pattern, self.happy_hour_times, re.IGNORECASE)

        if not match:
            return None, None

        start_hour, start_min, start_period = int(match.group(1)), int(match.group(2)), match.group(3).upper()
        end_hour, end_min, end_period = int(match.group(4)), int(match.group(5)), match.group(6).upper()

        # 24-hour format
        if start_period == 'PM' and start_hour != 12:
            start_hour += 12
        elif start_period == 'AM' and start_hour == 12:
            start_hour = 0

        if end_period == 'PM' and end_hour != 12:
            end_hour += 12
        elif end_period == 'AM' and end_hour == 12:
            end_hour = 0

        return time(start_hour, start_min), time(end_hour, end_min)

    def __str__(self) -> str:
        """String representation of venue"""
        status = "OPEN NOW" if self.is_open_now() else "CLOSED"
        stars = "⭐" * int(self.rating) + "☆" * (5 - int(self.rating))

        return f"""
{self.name} ({self.neighborhood})
{stars} ({self.rating}/5.0)
Happy Hour: {self.happy_hour_days}, {self.happy_hour_times}
Offers: {self.offers}
Status: {status}
"""

class HappyHourTracker:
    """Main application class for managing happy hour venues"""

    def __init__(self, data_file: str = "happy_hour_venues.json"):
        self.data_file = data_file
        self.venues: List[HappyHourVenue] = []
        self.load_data()

    def load_data(self):
        """Load venues from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.venues = [HappyHourVenue.from_dict(venue_data) for venue_data in data]
                print(f"Loaded {len(self.venues)} venues from {self.data_file}")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading data: {e}")
                self.venues = []
        else:
            # sample data
            self._create_sample_data()
            self.save_data()

    def save_data(self):
        """Save venues to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump([venue.to_dict() for venue in self.venues], f, indent=2)
            print(f"Data saved to {self.data_file}")
        except Exception as e:
            print(f"Error saving data: {e}")

    def _create_sample_data(self):
        """Create initial sample venues"""
        sample_venues = [
            HappyHourVenue("Castas Rum Bar", "Foggy Bottom", "Mon-Fri", "5:00 PM - 7:00 PM",
                          4.5, "$5 beer, $10 mojitos & frozens, $40 pitchers"),
            HappyHourVenue("Georgetown Piano Bar", "Georgetown", "Wed-Sun", "5:00 PM - 7:00 PM",
                          4.2, "Half price appetizers, $5 draft beer"),
            HappyHourVenue("Bar Chinois", "Chinatown", "Mon-Sun", "5:00 PM - 7:00 PM",
                          4.3, "$1 dumplings, discounted cocktails"),
            HappyHourVenue("Silver Diner", "Navy Yard", "Mon-Sun", "3:00 PM - 9:00 PM",
                          4.7, "$4 beers, , $7 wines, $8 cocktails")
        ]
        self.venues = sample_venues

    def add_venue(self, name: str, neighborhood: str, happy_hour_days: str,
                  happy_hour_times: str, rating: float, offers: str) -> bool:
        """Add a new venue"""
        # Check if venue already exists
        if any(venue.name.lower() == name.lower() for venue in self.venues):
            print(f"Venue '{name}' already exists!")
            return False

        # Validate rating
        if not (1.0 <= rating <= 5.0):
            print("Rating must be between 1.0 and 5.0")
            return False

        new_venue = HappyHourVenue(name, neighborhood, happy_hour_days,
                                  happy_hour_times, rating, offers)
        self.venues.append(new_venue)
        self.save_data()
        print(f"Added venue: {name}")
        return True

    def update_rating(self, venue_name: str, new_rating: float) -> bool:
        """Update a venue's rating"""
        venue = self._find_venue(venue_name)
        if not venue:
            print(f"Venue '{venue_name}' not found!")
            return False

        if not (1.0 <= new_rating <= 5.0):
            print("Rating must be between 1.0 and 5.0")
            return False

        old_rating = venue.rating
        venue.rating = new_rating
        self.save_data()
        print(f"Updated {venue_name} rating from {old_rating} to {new_rating}")
        return True

    def delete_venue(self, venue_name: str) -> bool:
        """Delete a venue"""
        venue = self._find_venue(venue_name)
        if not venue:
            print(f"Venue '{venue_name}' not found!")
            return False

        self.venues.remove(venue)
        self.save_data()
        print(f"Deleted venue: {venue_name}")
        return True

    def _find_venue(self, venue_name: str) -> Optional[HappyHourVenue]:
        """Find venue by name (case insensitive)"""
        for venue in self.venues:
            if venue.name.lower() == venue_name.lower():
                return venue
        return None

    def get_open_venues(self) -> List[HappyHourVenue]:
        """Get all currently open venues"""
        return [venue for venue in self.venues if venue.is_open_now()]

    def get_venues_by_rating(self, min_rating: float = 0.0) -> List[HappyHourVenue]:
        """Get venues sorted by rating (highest first)"""
        filtered = [venue for venue in self.venues if venue.rating >= min_rating]
        return sorted(filtered, key=lambda v: v.rating, reverse=True)

    def get_venues_by_neighborhood(self, neighborhood: str = None) -> List[HappyHourVenue]:
        """Get venues in a specific neighborhood"""
        if neighborhood:
            return [venue for venue in self.venues
                   if venue.neighborhood.lower() == neighborhood.lower()]
        else:
            return sorted(self.venues, key=lambda v: v.neighborhood)

    def display_venues(self, venues: List[HappyHourVenue], title: str = "Venues"):
        """Display a list of venues"""
        if not venues:
            print(f"\nNo venues found for: {title}")
            return

        print(f"\n{'='*50}")
        print(f"{title.upper()} ({len(venues)} venues)")
        print(f"{'='*50}")

        for i, venue in enumerate(venues, 1):
            print(f"{i}. {venue}")
            print("-" * 40)

    def display_current_status(self):
        """Display current time and open venues"""
        now = datetime.now()
        print(f"\n Current Time: {now.strftime('%A, %B %d, %Y at %I:%M %p')}")

        open_venues = self.get_open_venues()
        if open_venues:
            self.display_venues(open_venues, "Currently Open Happy Hours")
        else:
            print("\n No happy hours are currently open.")

    def interactive_menu(self):
        """Run the interactive command-line interface"""
        while True:
            print(f"\n{'='*50}")
            print("DC HAPPY HOUR TRACKER")
            print(f"{'='*50}")
            print("1. View all venues")
            print("2. View currently open venues")
            print("3. View venues by rating")
            print("4. View venues by neighborhood")
            print("5. Add new venue")
            print("6. Update venue rating")
            print("7. Delete venue")
            print("8. Current status")
            print("9. Exit")

            choice = input("\nEnter your choice (1-9): ").strip()

            if choice == '1':
                self.display_venues(self.venues, "All Venues")

            elif choice == '2':
                open_venues = self.get_open_venues()
                self.display_venues(open_venues, "Currently Open Venues")

            elif choice == '3':
                min_rating = input("Enter minimum rating (1-5, or press Enter for all): ").strip()
                try:
                    min_rating = float(min_rating) if min_rating else 0.0
                    venues = self.get_venues_by_rating(min_rating)
                    self.display_venues(venues, f"Venues with rating >= {min_rating}")
                except ValueError:
                    print("Invalid rating entered!")

            elif choice == '4':
                neighborhood = input("Enter neighborhood (or press Enter for all): ").strip()
                venues = self.get_venues_by_neighborhood(neighborhood or None)
                title = f"Venues in {neighborhood}" if neighborhood else "All Venues by Neighborhood"
                self.display_venues(venues, title)

            elif choice == '5':
                self._add_venue_interactive()

            elif choice == '6':
                self._update_rating_interactive()

            elif choice == '7':
                self._delete_venue_interactive()

            elif choice == '8':
                self.display_current_status()

            elif choice == '9':
                print("Thanks for using DC Happy Hour Tracker! 🍻")
                break

            else:
                print("Invalid choice! Please enter 1-9.")

    def _add_venue_interactive(self):
        """Interactive venue addition"""
        print("\n--- Add New Venue ---")
        name = input("Venue name: ").strip()
        if not name:
            print("Venue name is required!")
            return

        neighborhood = input("Neighborhood: ").strip()
        if not neighborhood:
            print("Neighborhood is required!")
            return

        happy_hour_days = input("Happy hour days (e.g., 'Mon-Fri', 'Tue-Thu'): ").strip()
        if not happy_hour_days:
            print("Happy hour days are required!")
            return

        happy_hour_times = input("Happy hour times (e.g., '4:00 PM - 7:00 PM'): ").strip()
        if not happy_hour_times:
            print("Happy hour times are required!")
            return

        try:
            rating = float(input("Rating (1.0-5.0): ").strip())
        except ValueError:
            print("Invalid rating! Please enter a number between 1.0 and 5.0")
            return

        offers = input("Special offers: ").strip()
        if not offers:
            print("Special offers are required!")
            return

        self.add_venue(name, neighborhood, happy_hour_days, happy_hour_times, rating, offers)

    def _update_rating_interactive(self):
        """Interactive rating update"""
        print("\n--- Update Venue Rating ---")
        venue_name = input("Enter venue name: ").strip()
        if not venue_name:
            print("Venue name is required!")
            return

        try:
            new_rating = float(input("Enter new rating (1.0-5.0): ").strip())
            self.update_rating(venue_name, new_rating)
        except ValueError:
            print("Invalid rating! Please enter a number between 1.0 and 5.0")

    def _delete_venue_interactive(self):
        """Interactive venue deletion"""
        print("\n--- Delete Venue ---")
        venue_name = input("Enter venue name to delete: ").strip()
        if not venue_name:
            print("Venue name is required!")
            return

        confirm = input(f"Are you sure you want to delete '{venue_name}'? (y/N): ").strip().lower()
        if confirm == 'y':
            self.delete_venue(venue_name)
        else:
            print("Deletion cancelled.")

def main():
    """Main function to run the application"""
    tracker = HappyHourTracker()

    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == '--status':
            tracker.display_current_status()
        elif sys.argv[1] == '--open':
            open_venues = tracker.get_open_venues()
            tracker.display_venues(open_venues, "Currently Open Venues")
        elif sys.argv[1] == '--all':
            tracker.display_venues(tracker.venues, "All Venues")
        else:
            print("Available arguments: --status, --open, --all")
    else:
        tracker.interactive_menu()

if __name__ == "__main__":
    main()
