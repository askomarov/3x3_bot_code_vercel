"""
Vercel / Flask entrypoint: Telegram webhook → python-telegram-bot.
Локальный polling: python run_bot.py
"""
from __future__ import annotations

import asyncio
import logging
import threading

from flask import Flask, abort, jsonify, request
from telegram import Update

from app.bot import BasketballScorerBot
from app.config import (
    BOT_TOKEN,
    TELEGRAM_WEBHOOK_SECRET,
    resolve_webhook_url,
    validate_config,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Flask `app` должен существовать на импорте — иначе Vercel не видит entrypoint.
app = Flask(__name__)

_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)
_loop_lock = threading.Lock()
_ready = False
_bot = None
ptb = None


def _boot():
    """Не трогаем Telegram/Postgres на импорте — билд Vercel иначе падает без env."""
    global _bot, ptb
    if _bot is not None:
        return
    validate_config()
    _bot = BasketballScorerBot(BOT_TOKEN, webhook=True)
    ptb = _bot.application


def run_async(coro):
    _boot()
    with _loop_lock:
        return _loop.run_until_complete(coro)


async def _ensure_initialized():
    global _ready
    _boot()
    if not _ready:
        await ptb.initialize()
        _ready = True
        logger.info("PTB application initialized")


async def _process_update(payload: dict):
    await _ensure_initialized()
    update = Update.de_json(payload, ptb.bot)
    if update is None:
        return
    await ptb.process_update(update)


@app.get("/")
def health():
    return jsonify({"ok": True, "bot": "3x3-scorer"})


@app.post("/telegram")
def telegram_webhook():
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if TELEGRAM_WEBHOOK_SECRET and secret != TELEGRAM_WEBHOOK_SECRET:
        abort(403)
    payload = request.get_json(force=True, silent=True)
    if not payload:
        abort(400)
    run_async(_process_update(payload))
    return "", 200


@app.get("/setup-webhook")
def setup_webhook():
    """Один раз после деплоя: /setup-webhook?secret=<TELEGRAM_WEBHOOK_SECRET>"""
    secret = request.args.get("secret", "")
    if TELEGRAM_WEBHOOK_SECRET and secret != TELEGRAM_WEBHOOK_SECRET:
        abort(403)

    url = resolve_webhook_url()
    if not url:
        return jsonify({"ok": False, "error": "WEBHOOK_URL / VERCEL_URL is empty"}), 400

    async def _set():
        await _ensure_initialized()
        await ptb.bot.set_webhook(
            url=url,
            secret_token=TELEGRAM_WEBHOOK_SECRET or None,
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
        )
        return await ptb.bot.get_webhook_info()

    info = run_async(_set())
    return jsonify({
        "ok": True,
        "url": info.url,
        "pending_update_count": info.pending_update_count,
    })
