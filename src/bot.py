import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import os
from dotenv import load_dotenv

from src.core.commands.lesson_schedule import LessonSchedule

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=str(os.getenv("BOT_TOKEN")))
dp = Dispatcher()

# Cache for schedule managers
schedule_managers: Dict[str, LessonSchedule] = {}

# Turkish day names
TURKISH_DAYS = {
    0: "Pazartesi",
    1: "Salı",
    2: "Çarşamba",
    3: "Perşembe",
    4: "Cuma",
    5: "Cumartesi",
    6: "Pazar",
}


def format_date(date: datetime) -> str:
    """Format date as DD.MM.YYYY - Turkish Day Name"""
    return f"{date.strftime('%d.%m.%Y')} - {TURKISH_DAYS.get(date.weekday(), '')}"


async def get_schedule_info(
    schedule_manager: LessonSchedule, date: datetime
) -> Dict[str, Any]:
    """Get formatted schedule information for a date"""
    lessons = await schedule_manager.get_schedule(date)
    return {
        "date": date,
        "formatted_date": format_date(date),
        "lessons": lessons,
        "class_id": schedule_manager.class_id,
    }


async def get_next_day_info(
    schedule_manager: LessonSchedule, date: datetime
) -> Dict[str, Any]:
    """Get schedule for the next day"""
    return await get_schedule_info(schedule_manager, date + timedelta(days=1))


async def get_previous_day_info(
    schedule_manager: LessonSchedule, date: datetime
) -> Dict[str, Any]:
    """Get schedule for the previous day"""
    return await get_schedule_info(schedule_manager, date - timedelta(days=1))


def build_schedule_message(info: Dict[str, Any]) -> str:
    """Build schedule message from info dict"""
    class_id = info["class_id"]
    formatted_date = info["formatted_date"]
    lessons = info["lessons"]

    message = f"<b>🗓️ Ders Programı</b>\n<b>{class_id}</b>\n\n"
    message += f"<b><i>{formatted_date}</i></b>\n\n"

    if isinstance(lessons, list) and lessons:
        message += "\n".join(f"• {lesson}" for lesson in lessons) + "\n"
    else:
        message += "Bu gün ders yok.\n"

    return message


def build_navigation_keyboard(
    class_id: str, date_str: str
) -> types.InlineKeyboardMarkup:
    """Build navigation keyboard"""
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="⬅️ Önceki Gün",
                    callback_data=f"nav_{class_id}_prev_{date_str}",
                ),
                types.InlineKeyboardButton(
                    text="Sonraki Gün ➡️",
                    callback_data=f"nav_{class_id}_next_{date_str}",
                ),
            ],
            [
                types.InlineKeyboardButton(
                    text="🔙 Sınıf Seçimine Dön",
                    callback_data="back_to_class_selection",
                )
            ],
        ]
    )


def build_class_keyboard() -> types.InlineKeyboardMarkup:
    """Build class selection keyboard"""
    classes = ["10A", "10B", "10C"]
    buttons = [
        types.InlineKeyboardButton(text=cls, callback_data=f"class_{cls}")
        for cls in classes
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=[buttons])


# Command handlers
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    user = message.from_user.first_name if message.from_user else "there"
    text = f"""<b>Öğrenme Aracısı</b>

Merhaba {user}! Derslerinde ve okulunda sana yardımcı olacağım.

Başlamak için komut seç:

• /kitap – Ders kitaplarından herhangi bir sayfanın cevabını bul.
• /odev – Güncel ödevlerini ve yarına yapılacak ödevleri gör.
• /dersprogrami – Ders programını ve yarın hangi derslerin olduğunu incele."""
    await message.answer(text, parse_mode="HTML")


@dp.message(Command("dersprogrami"))
async def handle_dersprogrami(message: types.Message):
    text = """<b>🗓️ Ders Programı</b>

Ders programını incelemek istediğin sınıfı seç."""
    await message.answer(text, reply_markup=build_class_keyboard(), parse_mode="HTML")


@dp.message(Command("kitap"))
async def handle_kitap(message: types.Message):
    pass  # Placeholder


@dp.message(Command("odev"))
async def handle_odev(message: types.Message):
    pass  # Placeholder


# Callback handlers
@dp.callback_query(lambda c: c.data and c.data.startswith("class_"))
async def handle_class_selection(callback_query: types.CallbackQuery):
    try:
        selected_class = callback_query.data.split("_")[1]  # type: ignore

        if selected_class not in schedule_managers:
            schedule_managers[selected_class] = LessonSchedule(selected_class)
        schedule_manager = schedule_managers[selected_class]

        today = datetime.now()
        info = await get_schedule_info(schedule_manager, today)

        text = build_schedule_message(info)
        keyboard = build_navigation_keyboard(selected_class, today.strftime("%Y-%m-%d"))

        await bot.answer_callback_query(callback_query.id)
        if callback_query.message:
            await bot.edit_message_text(
                chat_id=callback_query.from_user.id,
                message_id=callback_query.message.message_id,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
    except Exception as e:
        logging.error(f"Error in handle_class_selection: {e}")
        await bot.answer_callback_query(
            callback_query.id,
            text="Bir hata oluştu. Lütfen tekrar deneyin.",
            show_alert=True,
        )


@dp.callback_query(lambda c: c.data and c.data.startswith("nav_"))
async def handle_day_navigation(callback_query: types.CallbackQuery):
    try:
        parts = callback_query.data.split("_")  # type: ignore
        selected_class = parts[1]
        direction = parts[2]
        current_date = datetime.strptime(parts[3], "%Y-%m-%d")

        schedule_manager = schedule_managers.get(selected_class)
        if not schedule_manager:
            schedule_managers[selected_class] = LessonSchedule(selected_class)
            schedule_manager = schedule_managers[selected_class]

        if direction == "prev":
            info = await get_previous_day_info(schedule_manager, current_date)
        else:
            info = await get_next_day_info(schedule_manager, current_date)

        text = build_schedule_message(info)
        date_str = info["date"].strftime("%Y-%m-%d")
        keyboard = build_navigation_keyboard(selected_class, date_str)

        await bot.answer_callback_query(callback_query.id)
        if callback_query.message:
            await bot.edit_message_text(
                chat_id=callback_query.from_user.id,
                message_id=callback_query.message.message_id,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
    except Exception as e:
        logging.error(f"Error in handle_day_navigation: {e}")
        await bot.answer_callback_query(
            callback_query.id,
            text="Bir hata oluştu. Lütfen tekrar deneyin.",
            show_alert=True,
        )


@dp.callback_query(lambda c: c.data == "back_to_class_selection")
async def handle_back_to_class_selection(callback_query: types.CallbackQuery):
    try:
        text = """<b>🗓️ Ders Programı</b>

Ders programını incelemek istediğin sınıfı seç."""
        keyboard = build_class_keyboard()

        await bot.answer_callback_query(callback_query.id)
        if callback_query.message:
            await bot.edit_message_text(
                chat_id=callback_query.from_user.id,
                message_id=callback_query.message.message_id,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
    except Exception as e:
        logging.error(f"Error in handle_back_to_class_selection: {e}")
        await bot.answer_callback_query(
            callback_query.id,
            text="Bir hata oluştu. Lütfen tekrar deneyin.",
            show_alert=True,
        )


async def set_commands(bot: Bot):
    commands = [
        types.BotCommand(
            command="start", description="Botu başlatır ve komutları listeler"
        ),
        types.BotCommand(
            command="dersprogrami", description="Ders programını gösterir"
        ),
        types.BotCommand(command="kitap", description="Kitap içeriği bulur"),
        types.BotCommand(command="odev", description="Ödevleri listeler"),
    ]
    await bot.set_my_commands(commands)


async def main():
    await set_commands(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
