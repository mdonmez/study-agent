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

        temp_instance = cls()
        headers = temp_instance._get_api_headers()

        response = httpx.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        classes = []
        for item in data:
            if item["type"] == "file" and item["name"].endswith(".json"):
                class_name = item["name"][:-5]
                classes.append(class_name)

        return sorted(classes)

    def get_schedule(self, class_id: str) -> dict[str, list[str]]:
        """Fetch schedule data from GitHub for a specific class."""
        url = f"{self.base_url}/{class_id}.json"
        headers = self._get_api_headers()

        try:
            response = httpx.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise IOError(f"Error fetching schedule data for {class_id}: {e}")


if __name__ == "__main__":
    manager = LessonSchedule()

    try:
        print(f"10A schedule: {manager.get_schedule('10A')}")
        print(f"10B schedule: {manager.get_schedule('10B')}")

    except Exception as e:
        print(f"Error: {e}")
