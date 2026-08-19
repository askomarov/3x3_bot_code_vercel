"""
Обработчики пользовательских команд
"""
import json
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes

from .base import BaseHandler
from ..config import WEBAPP_URL, WEBAPP_3PTS_URL, WEBAPP_TACTICAL_BOARD_URL, ADMIN_ID
from ..utils import format_game_result, format_all_games, validate_game_data, md2, md2_bold
from ..contest_utils import format_contest_result, validate_contest_data


class UserCommandHandlers(BaseHandler):
    """Обработчики команд для обычных пользователей"""

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        user = update.effective_user
        user_id = user.id

        self.log_user_action(update, "started bot")

        # Проверяем, новый ли это пользователь
        is_new = self.db.is_new_user(user_id)

        if is_new:
            # Регистрируем нового пользователя
            self.db.register_user(
                user_id=user_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )

            # Уведомляем админа о новом пользователе
            if ADMIN_ID and ADMIN_ID != user_id:
                try:
                    admin_message = f"""
🆕 **Новый пользователь зарегистрировался в боте!**

👤 **Информация о пользователе:**
• **ID:** `{user_id}`
• **Имя:** {user.first_name or 'Не указано'}
• **Фамилия:** {user.last_name or 'Не указана'}
• **Username:** @{user.username or 'Не указан'}

📅 **Время регистрации:** Только что
                    """
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=admin_message,
                        parse_mode='Markdown'
                    )
                    self.db.mark_user_notified(user_id)
                    self.logger.info(f"✅ Admin notified about new user: {user_id}")
                except Exception as e:
                    self.logger.error(f"❌ Failed to notify admin about new user {user_id}: {e}")

        welcome_text = f"""
🏀 Welcome to 3x3 Scorer, {user.first_name}!

This is a professional scorer for 3x3 basketball with support for:
• Keeping score for two teams
• Game timer (10 minutes)
• Statistics saving
• Game history

Press the button below to open the scorer:
        """
        keyboard = [
            [KeyboardButton("🏀 Open Scorer", web_app=WebAppInfo(WEBAPP_URL))],
            [KeyboardButton("🎯 3pts Contest", web_app=WebAppInfo(WEBAPP_3PTS_URL))],
            [KeyboardButton("Tactical Board", web_app=WebAppInfo(WEBAPP_TACTICAL_BOARD_URL))],
            [KeyboardButton("ℹ️ Help"), KeyboardButton("📊 All Games")],
            [KeyboardButton("🗑️ Clear Stats")]
        ]

        # Добавляем админские кнопки если это админ
        if self.is_admin(user_id):
            keyboard.append([KeyboardButton("👥 All Users"), KeyboardButton("📈 Bot Stats")])
            keyboard.append([KeyboardButton("🗑️ Admin Clear All")])

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help"""
        self.log_user_action(update, "requested help")

        help_text = "\n".join([
            md2_bold("🏀 3x3 Scorer - Help"),
            "",
            md2_bold("Main features:"),
            md2("• Keeping score for two teams"),
            md2("• Game timer (10 minutes) and shot clock (12 seconds)"),
            md2("• Game stats are saved and sent to you in a reply message"),
            md2("• Complete game history with timestamps"),
            "",
            md2_bold("Available functions:"),
            f"🏀 *{md2('Open Scorer')}* {md2('- Launch the web scoring interface')}",
            f"ℹ️ *{md2('Help')}* {md2('- Show detailed help and instructions')}",
            f"📊 *{md2('All Games')}* {md2('- View complete game history with timestamps')}",
            f"🗑️ *{md2('Clear Stats')}* {md2('- Delete all saved statistics (with confirmation)')}",
            "",
            md2_bold("How to use:"),
            md2('1. Press "🏀 Open Scorer" to start a new game'),
            md2("2. Enter team names and begin scoring"),
            md2("  - Click the main timer to start/stop the game and the shot clock"),
            md2("  - If the shot clock runs out, the game pauses automatically"),
            md2("  - Click the score field to add 1 point; minus button subtracts 1 point"),
            md2("  - Click the foul field to add a foul; minus button subtracts a foul"),
            md2("  - Clicking the score field also resets the shot clock"),
            md2("  - Click the shot clock to reset it manually"),
            md2('  - "New Game" or "Reset" stops the game and opens a confirmation modal'),
            md2("3. Game results are saved and sent to you in a reply"),
            md2('4. Use "📊 All Games" to review all past games'),
            md2('5. Use "🗑️ Clear Stats" to reset your statistics'),
            "",
            md2_bold("Game data includes:"),
            md2("• Team names and final scores"),
            md2("• Game duration and total points"),
            md2("• Winner determination"),
            md2("• Timestamp of each game"),
            "",
            md2("Have fun playing! 🎉"),
        ])
        await update.message.reply_text(help_text, parse_mode='MarkdownV2')

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /stats - показывает все игры"""
        await self.all_games_command(update, context)

    async def all_games_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды всех игр"""
        user_id = update.effective_user.id
        self.log_user_action(update, "viewed all games")

        all_games = self.db.get_all_user_games(user_id)

        if not all_games:
            text = md2(
                "📊 You don't have any saved games yet.\n\n"
                "Play a few games to see your game history!"
            )
        else:
            text = md2_bold(f"📊 All your games ({len(all_games)} total):") + "\n\n"
            text += format_all_games(all_games)

        await update.message.reply_text(text, parse_mode='MarkdownV2')

    def _create_main_keyboard(self, user_id: int) -> ReplyKeyboardMarkup:
        """Создание основной клавиатуры"""
        keyboard = [
            [KeyboardButton("🏀 Open Scorer", web_app=WebAppInfo(WEBAPP_URL))],
            [KeyboardButton("🎯 3pts Contest", web_app=WebAppInfo(WEBAPP_3PTS_URL))],
            [KeyboardButton("Tactical Board", web_app=WebAppInfo(WEBAPP_TACTICAL_BOARD_URL))],
            [KeyboardButton("ℹ️ Help"), KeyboardButton("📊 All Games")],
            [KeyboardButton("🗑️ Clear Stats")]
        ]
        # hidden KeyboardButton("🇷🇸 Tournaments in Serbia")

        # Добавляем админские кнопки если это админ
        if self.is_admin(user_id):
            keyboard.append([KeyboardButton("👥 All Users"), KeyboardButton("📈 Bot Stats")])
            keyboard.append([KeyboardButton("🗑️ Admin Clear All")])

        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    async def clear_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды очистки статистики"""
        user_id = update.effective_user.id
        self.log_user_action(update, "requested stats clear")

        # Проверяем есть ли у пользователя игры
        games_count = self.db.get_user_games_count(user_id)
        if games_count == 0:
            await update.message.reply_text("📊 You don't have any saved games to clear.")
            return

        # Подтверждение перед очисткой
        keyboard = [
            [KeyboardButton("✅ Yes, clear all"), KeyboardButton("❌ Cancel")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

        clear_warn = "\n".join([
            md2_bold("⚠️ Warning!"),
            "",
            md2(f"You have {games_count} saved games."),
            md2("Are you sure you want to delete all your game statistics?"),
            "",
            md2("This action cannot be undone!"),
        ])
        await update.message.reply_text(
            clear_warn,
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )

    async def confirm_clear_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Подтверждение и очистка всей статистики пользователя"""
        user_id = update.effective_user.id
        self.log_user_action(update, "confirmed stats clear")

        try:
            deleted_count = self.db.clear_user_stats(user_id)
            reply_markup = self._create_main_keyboard(user_id)

            cleared = "\n".join([
                md2_bold("✅ Statistics cleared!"),
                "",
                md2(f"{deleted_count} of YOUR games have been deleted."),
                md2("Your personal game history is now empty."),
            ])
            await update.message.reply_text(
                cleared,
                parse_mode='MarkdownV2',
                reply_markup=reply_markup
            )
        except Exception as e:
            self.logger.error(f"Error clearing user stats: {e}")
            await self.send_error_message(update, "❌ Error: Failed to clear statistics.")

    async def cancel_clear_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена очистки статистики"""
        user_id = update.effective_user.id
        self.log_user_action(update, "cancelled stats clear")

        reply_markup = self._create_main_keyboard(user_id)

        await update.message.reply_text(
            f"{md2_bold('❌ Cancelled')}\n\n{md2('Your statistics have not been changed.')}",
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )

    async def handle_webapp_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка данных от Mini App (3x3 Scorer или 3pts Contest)"""
        try:
            web_app_data = update.effective_message.web_app_data.data
            user_id = update.effective_user.id
            user_name = update.effective_user.first_name or "Unknown"

            # Логируем полученные данные
            self.logger.info(f"📥 Received WebApp data from user {user_name} (ID: {user_id})")
            self.logger.info(f"📋 Raw data: {web_app_data}")

            if not web_app_data:
                self.logger.warning(f"❌ No data received from WebApp for user {user_id}")
                await update.message.reply_text("❌ No data received from WebApp.")
                return

            try:
                data = json.loads(web_app_data)
                self.logger.info(f"✅ Parsed data: {data}")
            except json.JSONDecodeError as e:
                self.logger.error(f"❌ JSON decode error for user {user_id}: {e}")
                await update.message.reply_text("❌ Error: Invalid JSON data received from WebApp.")
                return

            # Определяем тип данных по наличию ключей
            is_contest = 'playerName' in data and 'shotsAttempted' in data
            is_game = 'team1Name' in data and 'team2Name' in data

            if is_contest:
                # Обработка данных конкурса 3pts
                await self._handle_contest_data(update, user_id, data)
            elif is_game:
                # Обработка данных игры 3x3
                await self._handle_game_data(update, user_id, data)
            else:
                self.logger.warning(f"❌ Unknown data type for user {user_id}: {data.keys()}")
                await update.message.reply_text("❌ Error: Unknown data type received.")
        except Exception as e:
            self.logger.error(f"❌ Unexpected error in handle_webapp_data: {e}")
            await update.message.reply_text("❌ Error: An unexpected error occurred while processing the WebApp data.")

    async def _handle_game_data(self, update: Update, user_id: int, game_data: dict):
        """Обработка данных игры 3x3"""
        # Проверка корректности данных
        is_valid, error_message = validate_game_data(game_data)
        if not is_valid:
            self.logger.warning(f"❌ Invalid game data for user {user_id}: {error_message}")
            await update.message.reply_text(f"❌ Error: {error_message}")
            return

        self.logger.info(f"✅ Game data validation passed for user {user_id}")

        # Сохранение результата игры
        try:
            self.db.save_game_result(user_id, game_data)
            self.logger.info(f"💾 Game result saved for user {user_id}")
            result_message = format_game_result(game_data)
            await update.message.reply_text(result_message, parse_mode='MarkdownV2')
            self.logger.info(f"📤 Game result sent to user {user_id}")
        except Exception as e:
            self.logger.error(f"❌ Failed to save game result for user {user_id}: {e}")
            await update.message.reply_text("❌ Error: Failed to process game result.")

    async def _handle_contest_data(self, update: Update, user_id: int, contest_data: dict):
        """Обработка данных конкурса 3pts"""
        # Проверка корректности данных
        is_valid, error_message = validate_contest_data(contest_data)
        if not is_valid:
            self.logger.warning(f"❌ Invalid contest data for user {user_id}: {error_message}")
            await update.message.reply_text(f"❌ Error: {error_message}")
            return

        self.logger.info(f"✅ Contest data validation passed for user {user_id}")

        # Отправка результата конкурса (без сохранения в БД)
        try:
            result_message = format_contest_result(contest_data)
            await update.message.reply_text(result_message, parse_mode='MarkdownV2')
            self.logger.info(f"📤 Contest result sent to user {user_id}")
        except Exception as e:
            self.logger.error(f"❌ Failed to send contest result for user {user_id}: {e}")
            await update.message.reply_text("❌ Error: Failed to process contest result.")
