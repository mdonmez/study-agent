from datetime import datetime, timedelta
import httpx


class LessonSchedule:
    known_classes = ["10A", "10B", "10C"]

    def __init__(self):
        self.base_url = "https://raw.githubusercontent.com/mdonmez/study-agent/refs/heads/master/data/schedules"

    @classmethod
    def get_available_classes(cls) -> list[str]:
        return cls.known_classes

    def _fetch_schedule_data(self, class_id: str) -> dict[str, list[str]]:
        """Fetch schedule data from GitHub for a specific class."""
        url = f"{self.base_url}/{class_id}.json"
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

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
