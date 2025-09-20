from datetime import datetime, timedelta
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Homework:
    def __init__(self):
        self.base_url = "https://raw.githubusercontent.com/mdonmez/study-agent/refs/heads/master/data/homeworks"
        self.api_base_url = (
            "https://api.github.com/repos/mdonmez/study-agent/contents/data/homeworks"
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
            "https://api.github.com/repos/mdonmez/study-agent/contents/data/homeworks"
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

    def _fetch_homework_data(self, class_id: str) -> list[dict[str, str]]:
        """Fetch homework data from GitHub for a specific class."""
        url = f"{self.base_url}/{class_id}.json"
        headers = self._get_api_headers()

        try:
            response = httpx.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise IOError(f"Error fetching homework data for {class_id}: {e}")

    def get_homework_list(self, class_id: str) -> dict[str, list[dict[str, str]]]:
        all_homeworks = self._fetch_homework_data(class_id)

        next_day_str = self._next_school_day().strftime("%Y-%m-%d")
        due_next_school_day = [
            hw for hw in all_homeworks if hw.get("deadline") == next_day_str
        ]

        return {"all": all_homeworks, "due_next_school_day": due_next_school_day}

    def _next_school_day(self) -> datetime:
        today = datetime.now()
        return (
            today + timedelta(days=2)
            if today.weekday() == 5
            else today + timedelta(days=1)
        )


if __name__ == "__main__":
    try:
        manager = Homework()
        classes = manager.get_available_classes()
        print(f"Available classes: {classes}")

        if classes:
            test_class = "10C"
            try:
                hw_data = manager.get_homework_list(test_class)
                print(f"\nHomework for class {test_class}:")
                print("All:", hw_data["all"])
                print("Due next school day:", hw_data["due_next_school_day"])
            except Exception as e:
                print(f"Error getting homework for {test_class}: {e}")
    except Exception as e:
        print(f"Error initializing: {e}")
