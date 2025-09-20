import logging
import os
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class StudyAgentBot:
    """Main bot class handling all commands and callbacks."""

    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        # User state tracking for book page input
        self.user_states = {}  # {user_id: {'command': 'kitap', 'subject': 'fizik'}}
        self._register_handlers()

    def _register_handlers(self):
        """Register all command and callback handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("kitap", self.kitap_command))
        self.application.add_handler(CommandHandler("odev", self.odev_command))
        self.application.add_handler(CommandHandler("program", self.program_command))

        # Message handler for page number input
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message)
        )

        # Callback query handler for all button interactions
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))

    async def handle_text_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle text messages, particularly page number input for books."""
        if not update.message or not update.effective_user or not update.message.text:
            return

        user_id = update.effective_user.id
        text = update.message.text.strip()

        # Check if user is in a state that expects page number input
        if (
            user_id in self.user_states
            and self.user_states[user_id].get("command") == "kitap"
        ):
            subject = self.user_states[user_id].get("subject")

            # Try to parse page number
            try:
                page_number = int(text)
                if 1 <= page_number <= 500:  # Reasonable page range
                    await self._show_book_page(update.message, subject, page_number)
                    # Clear user state after showing page
                    del self.user_states[user_id]
                else:
                    await update.message.reply_text(
                        "Lütfen 1-500 arasında geçerli bir sayfa numarası girin.",
                        parse_mode="Markdown",
                    )
            except ValueError:
                await update.message.reply_text(
                    "Lütfen geçerli bir sayfa numarası girin (örnek: 53).",
                    parse_mode="Markdown",
                )

    async def _show_book_page(self, message, subject: str, page_number: int):
        """Show book page content with dummy placeholder responses."""
        subject_names = {
            "matematik": "🔢 Matematik",
            "kimya": "🧪 Kimya",
            "biyoloji": "🧬 Biyoloji",
            "fizik": "🏃 Fizik",
            "ingilizce": "🌐 İngilizce",
            "tarih": "🏛️ Tarih",
            "edebiyat": "📚 Edebiyat",
        }

        # Dummy content based on subject and page
        content_templates = {
            "matematik": [
                "Bu sayfada geometri konuları işleniyor. Üçgen alan formülleri ve örnekler bulunuyor.",
                "Algebra konularından fonksiyonlar ele alınıyor. Doğrusal ve ikinci dereceden fonksiyon örnekleri var.",
                "Trigonometri konusu işleniyor. Sin, cos, tan fonksiyonları ve grafikleri gösteriliyor.",
            ],
            "kimya": [
                "Atomun yapısı konusu anlatılıyor. Proton, nötron ve elektron sayıları hesaplanıyor.",
                "Periyodik tablo özellikları işleniyor. Element grupları ve periyotlar açıklanıyor.",
                "Kimyasal bağlar konusu var. İyonik ve kovalent bağ örnekleri gösteriliyor.",
            ],
            "biyoloji": [
                "Hücre yapısı ve organelleri anlatılıyor. Mitokondri ve ribozom fonksiyonları açıklanıyor.",
                "Fotosentez olayı işleniyor. Işık ve karanlık reaksiyonları detaylandırılıyor.",
                "Genetik konularından DNA yapısı ele alınıyor. Replikasyon süreci anlatılıyor.",
            ],
            "fizik": [
                "Hareket konuları işleniyor. Hız ve ivme hesaplamaları örneklerle gösteriliyor.",
                "Elektrik konularından Ohm kanunu anlatılıyor. Direnç ve akım hesaplamaları var.",
                "Dalga hareketi konusu işleniyor. Frekans, periyot ve dalga boyu formülleri veriliyor.",
            ],
            "ingilizce": [
                "Past tense kullanımı anlatılıyor. Regular ve irregular verb örnekleri bulunuyor.",
                "Reading comprehension bölümü var. Metin okuma ve anlama egzersizleri veriliyor.",
                "Vocabulary konusu işleniyor. Günlük hayattan kelimeler ve anlamları listeli.",
            ],
            "tarih": [
                "Osmanlı İmparatorluğu dönemi anlatılıyor. Kuruluş dönemi olayları kronolojik sırada.",
                "I. Dünya Savaşı konusu işleniyor. Savaşın sebepleri ve sonuçları açıklanıyor.",
                "Cumhuriyet dönemi reformları anlatılıyor. Atatürk'ün yaptığı inkılaplar sıralanıyor.",
            ],
            "edebiyat": [
                "Tanzimat dönemi yazarları anlatılıyor. Namık Kemal ve eserleri hakkında bilgi veriliyor.",
                "Şiir türleri işleniyor. Gazel, kaside ve mesnevi örnekleri gösteriliyor.",
                "Roman analizi konusu var. Karakter, olay örgüsü ve tema analiz yöntemleri anlatılıyor.",
            ],
        }

        # Get content template for the subject
        templates = content_templates.get(
            subject, ["Bu konuda henüz içerik bulunmuyor."]
        )
        content = templates[page_number % len(templates)]

        # Navigation buttons for previous/next page and back to subject selection
        prev_page = page_number - 1 if page_number > 1 else 1
        next_page = page_number + 1

        keyboard = [
            [
                InlineKeyboardButton(
                    f"{prev_page} ←", callback_data=f"kitap_page_{subject}_{prev_page}"
                ),
                InlineKeyboardButton(
                    "Sayfa Seçimine Dön", callback_data=f"kitap_{subject}"
                ),
                InlineKeyboardButton(
                    f"→ {next_page}", callback_data=f"kitap_page_{subject}_{next_page}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "Ders Seçimine Dön", callback_data="kitap_back_to_subjects"
                )
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message_text = (
            f"**📖 Kitap**\n"
            f"**{subject_names.get(subject, subject.title())}**\n\n"
            f"**_Sayfa {page_number}_**\n\n"
            f"{content}"
        )

        await message.reply_text(
            message_text, reply_markup=reply_markup, parse_mode="Markdown"
        )

    async def _show_book_page_callback(self, query, subject: str, page_number: int):
        """Show book page content via callback query (edit existing message)."""
        subject_names = {
            "matematik": "🔢 Matematik",
            "kimya": "🧪 Kimya",
            "biyoloji": "🧬 Biyoloji",
            "fizik": "🏃 Fizik",
            "ingilizce": "🌐 İngilizce",
            "tarih": "🏛️ Tarih",
            "edebiyat": "📚 Edebiyat",
        }

        # Dummy content based on subject and page (same as _show_book_page)
        content_templates = {
            "matematik": [
                "Bu sayfada geometri konuları işleniyor. Üçgen alan formülleri ve örnekler bulunuyor.",
                "Algebra konularından fonksiyonlar ele alınıyor. Doğrusal ve ikinci dereceden fonksiyon örnekleri var.",
                "Trigonometri konusu işleniyor. Sin, cos, tan fonksiyonları ve grafikleri gösteriliyor.",
            ],
            "kimya": [
                "Atomun yapısı konusu anlatılıyor. Proton, nötron ve elektron sayıları hesaplanıyor.",
                "Periyodik tablo özellikları işleniyor. Element grupları ve periyotlar açıklanıyor.",
                "Kimyasal bağlar konusu var. İyonik ve kovalent bağ örnekleri gösteriliyor.",
            ],
            "biyoloji": [
                "Hücre yapısı ve organelleri anlatılıyor. Mitokondri ve ribozom fonksiyonları açıklanıyor.",
                "Fotosentez olayı işleniyor. Işık ve karanlık reaksiyonları detaylandırılıyor.",
                "Genetik konularından DNA yapısı ele alınıyor. Replikasyon süreci anlatılıyor.",
            ],
            "fizik": [
                "Hareket konuları işleniyor. Hız ve ivme hesaplamaları örneklerle gösteriliyor.",
                "Elektrik konularından Ohm kanunu anlatılıyor. Direnç ve akım hesaplamaları var.",
                "Dalga hareketi konusu işleniyor. Frekans, periyot ve dalga boyu formülleri veriliyor.",
            ],
            "ingilizce": [
                "Past tense kullanımı anlatılıyor. Regular ve irregular verb örnekleri bulunuyor.",
                "Reading comprehension bölümü var. Metin okuma ve anlama egzersizleri veriliyor.",
                "Vocabulary konusu işleniyor. Günlük hayattan kelimeler ve anlamları listeli.",
            ],
            "tarih": [
                "Osmanlı İmparatorluğu dönemi anlatılıyor. Kuruluş dönemi olayları kronolojik sırada.",
                "I. Dünya Savaşı konusu işleniyor. Savaşın sebepleri ve sonuçları açıklanıyor.",
                "Cumhuriyet dönemi reformları anlatılıyor. Atatürk'ün yaptığı inkılaplar sıralanıyor.",
            ],
            "edebiyat": [
                "Tanzimat dönemi yazarları anlatılıyor. Namık Kemal ve eserleri hakkında bilgi veriliyor.",
                "Şiir türleri işleniyor. Gazel, kaside ve mesnevi örnekleri gösteriliyor.",
                "Roman analizi konusu var. Karakter, olay örgüsü ve tema analiz yöntemleri anlatılıyor.",
            ],
        }

        # Get content template for the subject
        templates = content_templates.get(
            subject, ["Bu konuda henüz içerik bulunmuyor."]
        )
        content = templates[page_number % len(templates)]

        # Navigation buttons for previous/next page and back to subject selection
        prev_page = page_number - 1 if page_number > 1 else 1
        next_page = page_number + 1

        keyboard = [
            [
                InlineKeyboardButton(
                    f"{prev_page} ←", callback_data=f"kitap_page_{subject}_{prev_page}"
                ),
                InlineKeyboardButton(
                    "Sayfa Seçimine Dön", callback_data=f"kitap_{subject}"
                ),
                InlineKeyboardButton(
                    f"→ {next_page}", callback_data=f"kitap_page_{subject}_{next_page}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "Ders Seçimine Dön", callback_data="kitap_back_to_subjects"
                )
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message_text = (
            f"**📖 Kitap**\n"
            f"**{subject_names.get(subject, subject.title())}**\n\n"
            f"**_Sayfa {page_number}_**\n\n"
            f"{content}"
        )

        await query.edit_message_text(
            message_text, reply_markup=reply_markup, parse_mode="Markdown"
        )

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command with greeting and command list."""
        if not update.message:
            return

        start_message = (
            "**Öğrenme Aracısı**\n\n"
            "Merhaba! Derslerinde ve okulunda sana yardımcı olacağım.\n\n"
            "Başlamak için komut seç:\n\n"
            "• /kitap – Ders kitaplarından herhangi bir sayfanın cevabını bul.\n"
            "• /odev – Güncel ödevlerini ve yarına yapılacak ödevleri gör.\n"
            "• /program – Ders programını ve yarın hangi derslerin olduğunu incele."
        )

        await update.message.reply_text(start_message, parse_mode="Markdown")

    async def kitap_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /kitap command - Book content navigation."""
        if not update.message:
            return

        keyboard = [
            [InlineKeyboardButton("🔢 Matematik", callback_data="kitap_matematik")],
            [InlineKeyboardButton("🧪 Kimya", callback_data="kitap_kimya")],
            [InlineKeyboardButton("🧬 Biyoloji", callback_data="kitap_biyoloji")],
            [InlineKeyboardButton("🏃 Fizik", callback_data="kitap_fizik")],
            [InlineKeyboardButton("🌐 İngilizce", callback_data="kitap_ingilizce")],
            [InlineKeyboardButton("🏛️ Tarih", callback_data="kitap_tarih")],
            [InlineKeyboardButton("📚 Edebiyat", callback_data="kitap_edebiyat")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = "**📖 Kitap**\n\nKitap içeriği bulmak istediğin dersi seç."

        await update.message.reply_text(
            message, reply_markup=reply_markup, parse_mode="Markdown"
        )

    async def odev_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /odev command - Homework management."""
        if not update.message:
            return

        keyboard = [
            [
                InlineKeyboardButton("10/A", callback_data="odev_10a"),
                InlineKeyboardButton("10/B", callback_data="odev_10b"),
                InlineKeyboardButton("10/C", callback_data="odev_10c"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = "**✍🏻 Ödev**\n\nÖdevlerini öğrenmek istediğin sınıfı seç."

        await update.message.reply_text(
            message, reply_markup=reply_markup, parse_mode="Markdown"
        )

    async def program_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /program command - Schedule viewing."""
        if not update.message:
            return

        keyboard = [
            [
                InlineKeyboardButton("10/A", callback_data="program_10a"),
                InlineKeyboardButton("10/B", callback_data="program_10b"),
                InlineKeyboardButton("10/C", callback_data="program_10c"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = (
            "**🗓️ Ders Programı**\n\nDers programını incelemek istediğin sınıfı seç."
        )

        await update.message.reply_text(
            message, reply_markup=reply_markup, parse_mode="Markdown"
        )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all callback queries from inline keyboards."""
        query = update.callback_query
        if not query or not query.data:
            return

        await query.answer()

        callback_data = query.data

        # Route to appropriate handler based on callback data prefix
        if callback_data.startswith("kitap_"):
            await self._handle_kitap_callback(query, callback_data)
        elif callback_data.startswith("odev_"):
            await self._handle_odev_callback(query, callback_data)
        elif callback_data.startswith("program_"):
            await self._handle_program_callback(query, callback_data)

    async def _handle_kitap_callback(self, query, callback_data: str):
        """Handle book-related callbacks."""
        action = callback_data.replace("kitap_", "")

        if action in [
            "matematik",
            "kimya",
            "biyoloji",
            "fizik",
            "ingilizce",
            "tarih",
            "edebiyat",
        ]:
            # Subject selected, show page input interface and set user state
            user_id = query.from_user.id if query.from_user else None
            if user_id:
                self.user_states[user_id] = {"command": "kitap", "subject": action}

            subject_names = {
                "matematik": "🔢 Matematik",
                "kimya": "🧪 Kimya",
                "biyoloji": "🧬 Biyoloji",
                "fizik": "🏃 Fizik",
                "ingilizce": "🌐 İngilizce",
                "tarih": "🏛️ Tarih",
                "edebiyat": "📚 Edebiyat",
            }

            keyboard = [
                [
                    InlineKeyboardButton(
                        "Ders Seçimine Dön", callback_data="kitap_back_to_subjects"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            message = (
                f"**📖 Kitap**\n"
                f"**{subject_names[action]}**\n\n"
                f"Bir sayfa numarası gir (Örnek: 53)."
            )

            await query.edit_message_text(
                message, reply_markup=reply_markup, parse_mode="Markdown"
            )

        elif action.startswith("page_"):
            # Handle page navigation callbacks (e.g., "page_fizik_53")
            parts = action.split("_")
            if len(parts) >= 3:
                subject = parts[1]
                try:
                    page_number = int(parts[2])
                    # Edit the message to show the new page
                    await self._show_book_page_callback(query, subject, page_number)
                except (ValueError, IndexError):
                    pass

        elif action == "back_to_subjects":
            # Return to subject selection and clear user state
            user_id = query.from_user.id if query.from_user else None
            if user_id and user_id in self.user_states:
                del self.user_states[user_id]

            keyboard = [
                [InlineKeyboardButton("🔢 Matematik", callback_data="kitap_matematik")],
                [InlineKeyboardButton("🧪 Kimya", callback_data="kitap_kimya")],
                [InlineKeyboardButton("🧬 Biyoloji", callback_data="kitap_biyoloji")],
                [InlineKeyboardButton("🏃 Fizik", callback_data="kitap_fizik")],
                [InlineKeyboardButton("🌐 İngilizce", callback_data="kitap_ingilizce")],
                [InlineKeyboardButton("🏛️ Tarih", callback_data="kitap_tarih")],
                [InlineKeyboardButton("📚 Edebiyat", callback_data="kitap_edebiyat")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            message = "**📖 Kitap**\n\nKitap içeriği bulmak istediğin dersi seç."

            await query.edit_message_text(
                message, reply_markup=reply_markup, parse_mode="Markdown"
            )

    async def _handle_odev_callback(self, query, callback_data: str):
        """Handle homework-related callbacks."""
        action = callback_data.replace("odev_", "")

        if action in ["10a", "10b", "10c"]:
            # Class selected, show homework
            class_name = (
                action.upper().replace("A", "/A").replace("B", "/B").replace("C", "/C")
            )

            keyboard = [
                [
                    InlineKeyboardButton(
                        "Sınıf Seçimine Dön", callback_data="odev_back_to_classes"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Sample homework data (placeholder)
            homework_data = {
                "10/A": {
                    "all": [
                        "Matematik sayfa 42, 43",
                        "Fizik 58",
                        "İngilizce yazım ödev",
                    ],
                    "tomorrow": ["Matematik sayfa 42"],
                },
                "10/B": {
                    "all": ["Kimya 35", "Biyoloji sayfa 61", "Tarih özet yazma"],
                    "tomorrow": ["Kimya 35"],
                },
                "10/C": {
                    "all": [
                        "Matematik sayfa 45, 46",
                        "Kimya 62",
                        "Din Kültürü sayfa 48 üst kısım",
                    ],
                    "tomorrow": ["Kimya 62"],
                },
            }

            hw_data = homework_data.get(class_name, {"all": [], "tomorrow": []})

            all_hw = "\n".join([f"- {hw}" for hw in hw_data["all"]])
            tomorrow_hw = "\n".join([f"- {hw}" for hw in hw_data["tomorrow"]])

            message = (
                f"**✍🏻 Ödev**\n"
                f"**{class_name}**\n\n"
                f"**_Tüm Ödevler_**\n\n"
                f"{all_hw}\n\n"
                f"**_Yarına yetiştirilmesi gerekenler_**\n\n"
                f"{tomorrow_hw}"
            )

            await query.edit_message_text(
                message, reply_markup=reply_markup, parse_mode="Markdown"
            )

        elif action == "back_to_classes":
            # Return to class selection
            keyboard = [
                [
                    InlineKeyboardButton("10/A", callback_data="odev_10a"),
                    InlineKeyboardButton("10/B", callback_data="odev_10b"),
                    InlineKeyboardButton("10/C", callback_data="odev_10c"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            message = "**✍🏻 Ödev**\n\nÖdevlerini öğrenmek istediğin sınıfı seç."

            await query.edit_message_text(
                message, reply_markup=reply_markup, parse_mode="Markdown"
            )

    async def _handle_program_callback(self, query, callback_data: str):
        """Handle schedule-related callbacks."""
        action = callback_data.replace("program_", "")

        if action in ["10a", "10b", "10c"]:
            # Class selected, show today's schedule
            class_name = (
                action.upper().replace("A", "/A").replace("B", "/B").replace("C", "/C")
            )

            # Store class in context for navigation
            context_data = f"program_{action}_today"

            await self._show_schedule(query, class_name, "today", context_data)

        elif "_prev" in action:
            # Previous day navigation
            class_action = action.replace("_prev", "")
            class_name = (
                class_action.upper()
                .replace("A", "/A")
                .replace("B", "/B")
                .replace("C", "/C")
            )
            context_data = f"program_{class_action}_yesterday"

            await self._show_schedule(query, class_name, "yesterday", context_data)

        elif "_next" in action:
            # Next day navigation
            class_action = action.replace("_next", "")
            class_name = (
                class_action.upper()
                .replace("A", "/A")
                .replace("B", "/B")
                .replace("C", "/C")
            )
            context_data = f"program_{class_action}_tomorrow"

            await self._show_schedule(query, class_name, "tomorrow", context_data)

        elif action == "back_to_classes":
            # Return to class selection
            keyboard = [
                [
                    InlineKeyboardButton("10/A", callback_data="program_10a"),
                    InlineKeyboardButton("10/B", callback_data="program_10b"),
                    InlineKeyboardButton("10/C", callback_data="program_10c"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            message = (
                "**🗓️ Ders Programı**\n\nDers programını incelemek istediğin sınıfı seç."
            )

            await query.edit_message_text(
                message, reply_markup=reply_markup, parse_mode="Markdown"
            )

    async def _show_schedule(
        self, query, class_name: str, day_type: str, context_data: str
    ):
        """Show schedule for specific class and day."""
        # Sample schedule data (placeholder)
        schedules = {
            "yesterday": {
                "date": "18.09.2025 - Perşembe",
                "classes": [
                    "Beden",
                    "Beden",
                    "Fizik",
                    "Fizik",
                    "Felsefe",
                    "Felsefe",
                    "Müzik",
                    "Müzik",
                ],
            },
            "today": {
                "date": "19.09.2025 - Cuma",
                "classes": [
                    "Coğrafya",
                    "Coğrafya",
                    "Matematik",
                    "Matematik",
                    "Kimya",
                    "Kimya",
                    "Biyoloji",
                    "Biyoloji",
                ],
            },
            "tomorrow": {
                "date": "20.09.2025 - Cumartesi",
                "classes": [
                    "Matematik",
                    "Matematik",
                    "İngilizce",
                    "İngilizce",
                    "Tarih",
                    "Tarih",
                    "Edebiyat",
                    "Edebiyat",
                ],
            },
        }

        schedule = schedules.get(day_type, schedules["today"])
        class_list = "\n".join([f"- {cls}" for cls in schedule["classes"]])

        # Navigation buttons
        class_code = class_name.lower().replace("/", "")
        keyboard = [
            [
                InlineKeyboardButton(
                    "Önceki Gün", callback_data=f"program_{class_code}_prev"
                ),
                InlineKeyboardButton(
                    "Sonraki Gün", callback_data=f"program_{class_code}_next"
                ),
            ],
            [
                InlineKeyboardButton(
                    "Sınıf Seçimine Dön", callback_data="program_back_to_classes"
                )
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = (
            f"**🗓️ Ders Programı**\n"
            f"**{class_name}**\n\n"
            f"**_{schedule['date']}_**\n\n"
            f"{class_list}"
        )

        await query.edit_message_text(
            message, reply_markup=reply_markup, parse_mode="Markdown"
        )

    def run(self):
        """Start the bot."""
        logger.info("Starting Study Agent Bot...")
        self.application.run_polling()


def main():
    """Main function to start the bot."""
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN not found in environment variables!")
        return

    bot = StudyAgentBot(token)
    bot.run()


if __name__ == "__main__":
    main()
