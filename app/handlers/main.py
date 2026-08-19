"""
Главный класс обработчиков команд, объединяющий все модули
"""
from telegram import Update
from telegram.ext import ContextTypes

from .user_commands import UserCommandHandlers
from .admin_commands import AdminCommandHandlers
from .game_commands import GameCommandHandlers
from ..config import ADMIN_ID


class CommandHandlers:
    """Главный класс обработчиков команд для 3x3 Scorer Bot"""

    def __init__(self, db):
        self.db = db
        self.user_handlers = UserCommandHandlers(db)
        self.admin_handlers = AdminCommandHandlers(db)
        self.game_handlers = GameCommandHandlers(db)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.user_handlers.start_command(update, context)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.user_handlers.help_command(update, context)

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.user_handlers.stats_command(update, context)

    async def all_games_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.user_handlers.all_games_command(update, context)

    async def clear_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.user_handlers.clear_stats_command(update, context)

    async def confirm_clear_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.user_handlers.confirm_clear_stats(update, context)

    async def cancel_clear_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.user_handlers.cancel_clear_stats(update, context)

    async def handle_webapp_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.user_handlers.handle_webapp_data(update, context)

    async def all_users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.admin_handlers.all_users_command(update, context)

    async def bot_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.admin_handlers.bot_stats_command(update, context)

    async def admin_clear_all_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.admin_handlers.admin_clear_all_command(update, context)

    async def confirm_admin_clear_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.admin_handlers.confirm_admin_clear_all(update, context)

    async def cancel_admin_clear_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.admin_handlers.cancel_admin_clear_all(update, context)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        user_id = update.effective_user.id

        if text == "ℹ️ Help":
            await self.help_command(update, context)
        elif text == "🏀 Open Scorer":
            await update.message.reply_text("🏀 Opening scorer...")
        elif text == "📊 All Games":
            await self.all_games_command(update, context)
        elif text == "🗑️ Clear Stats":
            await self.clear_stats_command(update, context)
        elif text == "✅ Yes, clear all":
            await self.confirm_clear_stats(update, context)
        elif text == "❌ Cancel":
            await self.cancel_clear_stats(update, context)
        elif text == "👥 All Users" and user_id == ADMIN_ID:
            await self.all_users_command(update, context)
        elif text == "📈 Bot Stats" and user_id == ADMIN_ID:
            await self.bot_stats_command(update, context)
        elif text == "🚨 YES, DELETE EVERYTHING" and user_id == ADMIN_ID:
            await self.confirm_admin_clear_all(update, context)
        elif text == "🗑️ Admin Clear All" and user_id == ADMIN_ID:
            await self.admin_clear_all_command(update, context)
        else:
            reply_markup = self.user_handlers._create_main_keyboard(user_id)
            await update.message.reply_text(
                "Use buttons to navigate or open scorer:",
                reply_markup=reply_markup
            )
