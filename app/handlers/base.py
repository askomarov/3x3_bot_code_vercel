"""
Базовый класс для всех обработчиков команд
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class BaseHandler:
    """Базовый класс для всех обработчиков команд"""

    def __init__(self, db):
        """
        Инициализация базового обработчика

        Args:
            db: Экземпляр класса Database
        """
        self.db = db
        self.logger = logger

    def log_user_action(self, update: Update, action: str):
        """
        Логирование действий пользователя

        Args:
            update: Telegram Update объект
            action: Описание действия
        """
        user = update.effective_user
        user_name = user.first_name or "Unknown"
        user_id = user.id

        self.logger.info(f"👤 User {user_name} (ID: {user_id}) - {action}")

    async def send_error_message(self, update: Update, message: str = "❌ Произошла ошибка."):
        """
        Отправка сообщения об ошибке пользователю

        Args:
            update: Telegram Update объект
            message: Текст сообщения об ошибке
        """
        try:
            await update.message.reply_text(message)
        except Exception as e:
            self.logger.error(f"❌ Failed to send error message: {e}")

    def is_admin(self, user_id: int) -> bool:
        """
        Проверка, является ли пользователь администратором

        Args:
            user_id: ID пользователя

        Returns:
            bool: True если пользователь админ, False иначе
        """
        from ..config import ADMIN_ID
        return user_id == ADMIN_ID
