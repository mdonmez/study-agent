from datetime import datetime, timedelta
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LessonSchedule:
    def __init__(self):
        self.base_url = "https://raw.githubusercontent.com/mdonmez/study-agent/refs/heads/master/data/schedules"
        self.api_base_url = (
            "https://api.github.com/repos/mdonmez/study-agent/contents/data/schedules"
        )
        self.github_token = os.getenv("GITHUB_API_KEY")

    def _get_api_headers(self) -> dict[str, str]:
        """Get headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "study-agent/1.0",
        }
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        return headers

    @classmethod
    def get_available_classes(cls) -> list[str]:
        """Fetch available classes from GitHub API."""
        api_url = (
            "https://api.github.com/repos/mdonmez/study-agent/contents/data/schedules"
        )

        # Create a temporary instance to get headers
        temp_instance = cls()
        headers = temp_instance._get_api_headers()

        response = httpx.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Extract JSON filenames and remove .json extension
        classes = []
        for item in data:
            if item["type"] == "file" and item["name"].endswith(".json"):
                class_name = item["name"][:-5]  # Remove .json extension
                classes.append(class_name)

        return sorted(classes)

    def _fetch_schedule_data(self, class_id: str) -> dict[str, list[str]]:
        """Fetch schedule data from GitHub for a specific class."""
        url = f"{self.base_url}/{class_id}.json"
        headers = self._get_api_headers()

        try:
            response = httpx.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise IOError(f"Error fetching schedule data for {class_id}: {e}")

    def get_schedule(self, class_id: str, date: datetime) -> list[str]:
        """Get schedule for the specified class and date."""
        full_schedule = self._fetch_schedule_data(class_id)
        day = self._day_key(date)
        return [] if day in {"saturday", "sunday"} else full_schedule.get(day, [])

    def _day_key(self, date: datetime) -> str:
        return [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ][date.weekday()]


if __name__ == "__main__":
    manager = LessonSchedule()

    today = datetime.now()
    tomorrow = today + timedelta(days=1)

    try:
        print(f"10A Today's schedule: {manager.get_schedule('10A', today)}")
        print(f"10A Tomorrow's schedule: {manager.get_schedule('10A', tomorrow)}")
        print(f"10B Today's schedule: {manager.get_schedule('10B', today)}")

    except Exception as e:
        print(f"Error: {e}")
