"""Vercel file-based Python entry. Flask-пресет на корневом main.py даёт пустой билд."""
from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from main import app  # noqa: E402, F401
