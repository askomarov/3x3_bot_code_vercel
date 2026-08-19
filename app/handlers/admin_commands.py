"""
Обработчики админских команд
"""
import html

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes

from .base import BaseHandler
from ..config import WEBAPP_URL, WEBAPP_3PTS_URL, WEBAPP_TACTICAL_BOARD_URL
from ..utils import md2, md2_bold


class AdminCommandHandlers(BaseHandler):
    """Обработчики админских команд"""

    def _create_admin_keyboard(self) -> ReplyKeyboardMarkup:
        keyboard = [
            [KeyboardButton("🏀 Open Scorer", web_app=WebAppInfo(WEBAPP_URL))],
            [KeyboardButton("🎯 3pts Contest", web_app=WebAppInfo(WEBAPP_3PTS_URL))],
            [KeyboardButton("📋 Tactical Board", web_app=WebAppInfo(WEBAPP_TACTICAL_BOARD_URL))],
            [KeyboardButton("ℹ️ Help"), KeyboardButton("📊 All Games")],
            [KeyboardButton("🗑️ Clear Stats"), KeyboardButton("👥 All Users")],
            [KeyboardButton("📈 Bot Stats")],
            [KeyboardButton("🗑️ Admin Clear All")],
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    async def all_users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ You don't have permission to execute this command.")
            return

        self.log_user_action(update, "viewed all users (admin)")

        try:
            all_users = self.db.get_all_users()

            if not all_users:
                await update.message.reply_text("👥 No users found.")
                return

            message = f"👥 All bot users ({len(all_users)} users):\n\n"

            for i, user in enumerate(all_users, 1):
                try:
                    username_raw = user.get("username")
                    if username_raw and username_raw.strip():
                        username = f"@{username_raw}"
                    else:
                        username = "Not specified"

                    first_name = user.get("first_name") or ""
                    last_name = user.get("last_name") or ""
                    full_name = f"{first_name} {last_name}".strip()
                    if not full_name:
                        full_name = "Not specified"

                    user_message = f"{i}. {full_name}\n"
                    user_message += f"• ID: {user.get('user_id', 'Unknown')}\n"
                    user_message += f"• Username: {username}\n"
                    user_message += f"• Registration date: {user.get('first_seen', 'Unknown')}\n\n"

                    message += user_message

                    if len(message) > 3500:
                        await update.message.reply_text(message)
                        message = ""

                except Exception as user_error:
                    self.logger.error(f"Error processing user {i}: {user_error}")
                    continue

            if message:
                await update.message.reply_text(message)

        except Exception as e:
            self.logger.error(f"Error in all_users_command: {e}")
            await self.send_error_message(update, "❌ Error fetching users list.")

    async def bot_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ You don't have permission to execute this command.")
            return

        self.log_user_action(update, "viewed bot stats (admin)")

        try:
            stats = self.db.get_database_stats()
            all_users = self.db.get_all_users()
            total_users = stats.get("total_users", 0)
            total_games = stats.get("total_games", 0)

            most_active_user = None
            max_games = 0
            if total_users > 0:
                user_game_counts = [
                    (user["user_id"], self.db.get_user_games_count(user["user_id"]))
                    for user in all_users
                ]
                if user_game_counts:
                    most_active_user_id, max_games = max(user_game_counts, key=lambda x: x[1])
                    for user in all_users:
                        if user["user_id"] == most_active_user_id:
                            most_active_user = user
                            break

            avg = total_games / total_users if total_users > 0 else 0
            lines = [
                f"📈 <b>{html.escape('Статистика бота 3x3 Scorer', quote=False)}</b>",
                "",
                f"<b>{html.escape('👥 Пользователи:', quote=False)}</b>",
                f"• Всего пользователей: {total_users}",
                "",
                f"<b>{html.escape('🏀 Игры:', quote=False)}</b>",
                f"• Всего игр сыграно: {total_games}",
                f"• Среднее количество игр на пользователя: {avg:.1f}",
                "",
                f"<b>{html.escape('🏆 Самый активный пользователь:', quote=False)}</b>",
            ]

            if most_active_user:
                full_name = f"{most_active_user['first_name'] or ''} {most_active_user['last_name'] or ''}".strip()
                username = f"@{most_active_user['username']}" if most_active_user["username"] else "Not specified"
                disp = full_name or "Name not specified"
                lines.append(
                    f"• {html.escape(disp, quote=False)} ({html.escape(username, quote=False)})"
                )
                lines.append(f"• ID: <code>{most_active_user['user_id']}</code>")
                lines.append(f"• Games played: {max_games}")
            else:
                lines.append(f"• {html.escape('Пока нет активных игроков', quote=False)}")

            await update.message.reply_text("\n".join(lines), parse_mode="HTML")

        except Exception as e:
            self.logger.error(f"❌ Error in bot_stats_command: {e}")
            await self.send_error_message(update, "❌ Error fetching bot stats.")

    async def admin_clear_all_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ You don't have permission to execute this command.")
            return

        self.log_user_action(update, "requested admin clear all (admin)")

        try:
            all_users = self.db.get_all_users()
            total_users = len(all_users)
            total_games = self.db.get_database_stats().get("total_games", 0)

            if total_users == 0 and total_games == 0:
                await update.message.reply_text("📊 Database is already empty.")
                return

            keyboard = [
                [KeyboardButton("🚨 YES, DELETE EVERYTHING"), KeyboardButton("❌ Cancel")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

            warn_body = "\n".join([
                md2_bold("🚨 CRITICAL WARNING!"),
                "",
                md2("You are about to delete ALL bot data:"),
                md2(f"• {total_users} users"),
                md2(f"• {total_games} games"),
                "",
                md2_bold("THIS ACTION IS IRREVERSIBLE!"),
                "",
                md2("Are you sure you want to delete all data?"),
            ])
            await update.message.reply_text(
                warn_body,
                parse_mode="MarkdownV2",
                reply_markup=reply_markup
            )

        except Exception as e:
            self.logger.error(f"❌ Error in admin_clear_all_command: {e}")
            await self.send_error_message(update, "❌ Error fetching data info.")

    async def confirm_admin_clear_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id

        if not self.is_admin(user_id):
            await update.message.reply_text("❌ You don't have permission to execute this command.")
            return

        self.log_user_action(update, "confirmed admin clear all (admin)")

        try:
            deleted_games = self.db.get_database_stats().get("total_games", 0)
            deleted_users = self.db.get_database_stats().get("total_users", 0)
            if hasattr(self.db, "clear_all_data"):
                self.db.clear_all_data()
            else:
                for user in self.db.get_all_users():
                    self.db.clear_user_stats(user["user_id"])

            reply_markup = self._create_admin_keyboard()

            cleared_body = "\n".join([
                md2_bold("🗑️ ALL DATA DELETED!"),
                "",
                md2("Deleted:"),
                md2(f"• {deleted_games} games"),
                md2(f"• {deleted_users} users"),
                "",
                md2("Bot database has been completely cleared."),
            ])
            await update.message.reply_text(
                cleared_body,
                parse_mode="MarkdownV2",
                reply_markup=reply_markup
            )

        except Exception as e:
            self.logger.error(f"❌ Error in confirm_admin_clear_all: {e}")
            await self.send_error_message(update, "❌ Error clearing data.")

    async def cancel_admin_clear_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self.log_user_action(update, "cancelled admin clear all")

        reply_markup = self._create_admin_keyboard()

        await update.message.reply_text(
            f"{md2_bold('❌ Canceled')}\n\n{md2('Bot data has not been changed.')}",
            parse_mode="MarkdownV2",
            reply_markup=reply_markup
        )
