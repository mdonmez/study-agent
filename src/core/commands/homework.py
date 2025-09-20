from datetime import datetime, timedelta
import httpx


class Homework:
    known_classes = ["10A", "10B", "10C"]

    def __init__(self):
        self.base_url = "https://raw.githubusercontent.com/mdonmez/study-agent/refs/heads/master/data/homeworks"

    @classmethod
    def get_available_classes(cls) -> list[str]:
        return cls.known_classes

    def _fetch_homework_data(self, class_id: str) -> list[dict[str, str]]:
        """Fetch homework data from GitHub for a specific class."""
        url = f"{self.base_url}/{class_id}.json"

        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

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
    manager = Homework()
    classes = manager.get_available_classes()

    if classes:
        test_class = "10C"
        try:
            hw_data = manager.get_homework_list(test_class)
            print(f"\nHomework for class {test_class}:")
            print("All:", hw_data["all"])
            print("Due next school day:", hw_data["due_next_school_day"])
        except Exception as e:
            print(f"Error getting homework for {test_class}: {e}")
