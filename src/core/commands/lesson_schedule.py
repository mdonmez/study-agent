import httpx
from datetime import datetime, timedelta


class LessonSchedule:
    def __init__(self, class_id: str):
        self.class_id = class_id
        self.BASE_URL = "https://raw.githubusercontent.com/mdonmez/study-agent/refs/heads/master/data/schedules"
        url = f"{self.BASE_URL}/{self.class_id}.json"
        response = httpx.get(
            url,
            headers={
                "User-Agent": "study-agent/1.0",
            },
            timeout=10,
        )
        response.raise_for_status()
        self.schedule_data = response.json()

    def get_schedule(self, date: datetime) -> list[str]:
        weekday_map = {
            0: "monday",
            1: "tuesday",
            2: "wednesday",
            3: "thursday",
            4: "friday",
            5: "saturday",
            6: "sunday",
        }
        day_name = weekday_map.get(date.weekday())
        return self.schedule_data.get(day_name, [])


if __name__ == "__main__":
    manager = LessonSchedule("10A")
    today = datetime.now()
    print(manager.get_schedule(today))

    days_ahead = 0 - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    next_monday = today + timedelta(days_ahead)
    print(manager.get_schedule(next_monday))
