"""
Конфигурация для 3x3 Scorer Bot
"""
import os
from dotenv import load_dotenv

load_dotenv()

IS_VERCEL = os.getenv("VERCEL") == "1"

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
WEBAPP_3PTS_URL = os.getenv("WEBAPP_3PTS_URL")
WEBAPP_TACTICAL_BOARD_URL = os.getenv("WEBAPP_TACTICAL_BOARD_URL")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

DATABASE_URL = os.getenv("DATABASE_URL")
PGHOST = os.getenv("PGHOST")
PGPORT = os.getenv("PGPORT", "5432")
PGDATABASE = os.getenv("PGDATABASE")
PGUSER = os.getenv("PGUSER")
PGPASSWORD = os.getenv("PGPASSWORD")
PGSSLMODE = os.getenv("PGSSLMODE")

FORCE_SQLITE = os.getenv("FORCE_SQLITE", "False").lower() == "true"
USE_POSTGRES_OVERRIDE = os.getenv("USE_POSTGRES")

if IS_VERCEL:
    FORCE_SQLITE = False
    USE_POSTGRES = True
elif FORCE_SQLITE:
    USE_POSTGRES = False
elif USE_POSTGRES_OVERRIDE is not None:
    USE_POSTGRES = USE_POSTGRES_OVERRIDE.lower() == "true"
else:
    USE_POSTGRES = bool(DATABASE_URL or (PGHOST and PGDATABASE and PGUSER and PGPASSWORD))


def resolve_webhook_url() -> str:
    """Явный WEBHOOK_URL, иначе production URL Vercel."""
    if WEBHOOK_URL:
        return WEBHOOK_URL.rstrip("/")
    host = os.getenv("VERCEL_PROJECT_PRODUCTION_URL") or os.getenv("VERCEL_URL")
    if host:
        return f"https://{host}/telegram"
    return ""


def validate_config():
    if not BOT_TOKEN:
        raise ValueError("❌ Error: BOT_TOKEN not found in environment variables")

    if not WEBAPP_URL:
        raise ValueError("❌ Error: WEBAPP_URL is missing")

    if IS_VERCEL and not (DATABASE_URL or (PGHOST and PGDATABASE and PGUSER and PGPASSWORD)):
        raise ValueError("❌ Error: Vercel requires Postgres (DATABASE_URL)")

    return True
