"""
Handlers module for 3x3 Scorer Bot
Разделение обработчиков команд на логические модули
"""

from .base import BaseHandler
from .user_commands import UserCommandHandlers
from .admin_commands import AdminCommandHandlers
from .game_commands import GameCommandHandlers
from .main import CommandHandlers

__all__ = [
    'BaseHandler',
    'UserCommandHandlers',
    'AdminCommandHandlers',
    'GameCommandHandlers',
    'CommandHandlers'
]
