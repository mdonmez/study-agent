from pathlib import Path
from datetime import datetime, timedelta
import json


class HomeworkManager:
    def __init__(self):
        self.project_root = Path(__file__).parents[3]
        self.homework_dir = self.project_root / "data" / "homeworks"

    @classmethod
    def get_available_classes(cls) -> list[str]:
        homework_dir = Path(__file__).parents[3] / "data" / "homeworks"
        return (
            sorted(f.stem for f in homework_dir.glob("*.json"))
            if homework_dir.exists()
            else []
        )

    def get_homework_list(self, class_id: str) -> dict[str, list[dict[str, str]]]:
        file_path = self.homework_dir / f"{class_id}.json"
        if not file_path.exists():
            return {"all": [], "due_next_school_day": []}

        try:
            all_homeworks = json.loads(file_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {"all": [], "due_next_school_day": []}

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
    manager = HomeworkManager()
    classes = manager.get_available_classes()
    print("Available classes:", classes)

    if classes:
        test_class = classes[0]
        hw_data = manager.get_homework_list(test_class)
        print(f"\nHomework for class {test_class}:")
        print("All:", hw_data["all"])
        print("Due next school day:", hw_data["due_next_school_day"])
