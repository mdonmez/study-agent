from datetime import datetime, timedelta
import httpx


class Homework:
    def __init__(self, class_id: str):
        self.class_id = class_id
        self.BASE_URL = "https://raw.githubusercontent.com/mdonmez/study-agent/refs/heads/master/data/homeworks"
        url = f"{self.BASE_URL}/{self.class_id}.json"
        response = httpx.get(
            url,
            headers={
                "User-Agent": "study-agent/1.0",
            },
            timeout=10,
        )
        response.raise_for_status()
        self.homework_data = response.json()

    def _next_school_day(self) -> datetime:
        today = datetime.now()
        return (
            today + timedelta(days=2)
            if today.weekday() == 5
            else today + timedelta(days=1)
        )

    def get_homework_list(self, due_next_day: bool = False) -> list[dict[str, str]]:
        all_homeworks = self.homework_data
        if due_next_day:
            next_day_str = self._next_school_day().strftime("%Y-%m-%d")
            return [hw for hw in all_homeworks if hw.get("deadline") == next_day_str]
        return all_homeworks


if __name__ == "__main__":
    manager = Homework("10C")

    print(manager.get_homework_list())
    print(manager.get_homework_list(due_next_day=True))
