"""
Основной файл для запуска 3x3 Scorer Telegram Bot
"""
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from .config import BOT_TOKEN, WEBAPP_URL, validate_config
from .database import Database
from .handlers import CommandHandlers
from .utils import is_valid_url

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)


class BasketballScorerBot:
    """Основной класс бота для ведения счета в баскетболе 3x3"""

    def __init__(self, token, *, webhook: bool = False):
        self.token = token
        builder = Application.builder().token(token)
        if webhook:
            builder = builder.updater(None)
        self.application = builder.build()
        self.db = Database()
        self.handlers = CommandHandlers(self.db)
        self.setup_handlers()

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.handlers.start_command))
        self.application.add_handler(CommandHandler("help", self.handlers.help_command))
        self.application.add_handler(CommandHandler("stats", self.handlers.stats_command))
        self.application.add_handler(CommandHandler("clear", self.handlers.clear_stats_command))

        self.application.add_handler(CommandHandler("users", self.handlers.all_users_command))
        self.application.add_handler(CommandHandler("botstats", self.handlers.bot_stats_command))
        self.application.add_handler(CommandHandler("adminclear", self.handlers.admin_clear_all_command))

        self.application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, self.handlers.handle_webapp_data))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_message))

    def run(self):
        logger.info("🏀 3x3 Scorer Bot started successfully!")
        print("🏀 3x3 Scorer Bot started successfully!")
        self.application.run_polling()


def main():
    try:
        validate_config()

        if not is_valid_url(WEBAPP_URL):
            print("❌ Error: WEBAPP_URL is invalid (must be HTTPS)")
            return

        print("🚀 Starting 3x3 Scorer Bot...")

        bot = BasketballScorerBot(BOT_TOKEN)
        bot.run()

    except ValueError as e:
        print(e)
    except KeyboardInterrupt:
        print("\n⏹️  Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")


if __name__ == "__main__":
    main()
