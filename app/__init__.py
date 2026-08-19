"""
3x3 Scorer Telegram Bot

Профессиональный бот для ведения счета в баскетболе 3x3
"""

from __future__ import annotations

__version__ = "1.0.0"
__author__ = "3x3 Scorer Bot Team"

__all__ = [
    "main",
    "BasketballScorerBot",
    "Database",
    "CommandHandlers",
    "BOT_TOKEN",
    "WEBAPP_URL",
    "WEBAPP_3PTS_URL",
    "WEBAPP_TACTICAL_BOARD_URL",
    "ADMIN_ID",
]


def __getattr__(name: str):
    if name == "main":
        from .bot import main as m

        return m
    if name == "BasketballScorerBot":
        from .bot import BasketballScorerBot as c

        return c
    if name == "Database":
        from .database import Database as d

        return d
    if name == "CommandHandlers":
        from .handlers import CommandHandlers as h

        return h
    if name in (
        "BOT_TOKEN",
        "WEBAPP_URL",
        "WEBAPP_3PTS_URL",
        "WEBAPP_TACTICAL_BOARD_URL",
        "ADMIN_ID",
    ):
        from . import config

        return getattr(config, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
