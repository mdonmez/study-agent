import asyncio
import httpx
from datetime import datetime, timedelta


class LessonSchedule:
    def __init__(self, class_id: str):
        self.class_id = class_id
        self.BASE_URL = "https://raw.githubusercontent.com/mdonmez/study-agent/refs/heads/master/data/schedules"

        url = f"{self.BASE_URL}/{self.class_id}.json"
        with httpx.Client() as client:
            response = client.get(
                url,
                headers={
                    "User-Agent": "study-agent/1.0",
                },
                timeout=10,
            )
            response.raise_for_status()
            self.schedule_data = response.json()

    async def get_schedule(self, date: datetime) -> list[str]:
        day_num = date.isoweekday()
        if day_num <= 5:
            return self.schedule_data.get(str(day_num), [])
        else:
            return []


if __name__ == "__main__":

    async def main():
        manager = LessonSchedule("10A")
        today = datetime.now()
        print(await manager.get_schedule(today))

        days_ahead = 0 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_monday = today + timedelta(days_ahead)
        print(await manager.get_schedule(next_monday))

    asyncio.run(main())
