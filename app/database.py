"""
Работа с базой данных для 3x3 Scorer Bot
"""
import json
import sqlite3

from .config import USE_POSTGRES

# Импортируем PostgreSQL обработчик только если нужно
if USE_POSTGRES:
    try:
        from .postgres_db import PostgresDatabase
    except ImportError as e:
        print(f"PostgreSQL dependencies not installed: {e}")
        USE_POSTGRES = False


class SQLiteDatabase:
    """Локальный обработчик SQLite (fallback для разработки)."""

    def __init__(self, db_path: str = "user_data.db"):
        self.db_path = db_path
        self.setup_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def setup_db(self):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    game_data TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_notified INTEGER DEFAULT 0
                )
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_games_user_id ON games(user_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_games_timestamp ON games(timestamp DESC)")
            conn.commit()
        print(f"SQLite database initialized successfully: {self.db_path}")

    def save_game_result(self, user_id: int, game_data: dict):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO games (user_id, game_data) VALUES (?, ?)",
                (user_id, json.dumps(game_data, ensure_ascii=False)),
            )
            conn.commit()

    def get_all_user_games(self, user_id: int) -> list:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT game_data, timestamp FROM games WHERE user_id = ? ORDER BY timestamp DESC",
                (user_id,),
            )
            rows = cur.fetchall()

        games = []
        for game_json, timestamp in rows:
            try:
                game = json.loads(game_json)
            except Exception:
                continue
            game["timestamp"] = timestamp
            games.append(game)
        return games

    def get_user_games_count(self, user_id: int) -> int:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM games WHERE user_id = ?", (user_id,))
            return cur.fetchone()[0]

    def clear_user_stats(self, user_id: int) -> int:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM games WHERE user_id = ?", (user_id,))
            count = cur.fetchone()[0]
            cur.execute("DELETE FROM games WHERE user_id = ?", (user_id,))
            conn.commit()
            return count

    def is_new_user(self, user_id: int) -> bool:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            return cur.fetchone() is None

    def register_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> bool:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO users (user_id, username, first_name, last_name, is_notified)
                VALUES (?, ?, ?, ?, 0)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    is_notified = 0
                """,
                (user_id, username, first_name, last_name),
            )
            conn.commit()
            return True

    def mark_user_notified(self, user_id: int):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE users SET is_notified = 1 WHERE user_id = ?", (user_id,))
            conn.commit()

    def get_all_users(self) -> list:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT user_id, username, first_name, last_name, first_seen
                FROM users
                ORDER BY first_seen DESC
                """
            )
            rows = cur.fetchall()

        return [
            {
                "user_id": row[0],
                "username": row[1],
                "first_name": row[2],
                "last_name": row[3],
                "first_seen": row[4],
            }
            for row in rows
        ]

    def get_database_stats(self) -> dict:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users")
            total_users = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM games")
            total_games = cur.fetchone()[0]

            cur.execute(
                "SELECT user_id, timestamp FROM games ORDER BY timestamp DESC LIMIT 5"
            )
            recent_games = [
                {"user_id": row[0], "timestamp": row[1]}
                for row in cur.fetchall()
            ]

        return {
            "database_type": "SQLite",
            "total_users": total_users,
            "total_games": total_games,
            "recent_games": recent_games,
        }

    def clear_all_data(self):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM games")
            cur.execute("DELETE FROM users")
            conn.commit()

    def test_connection(self) -> bool:
        try:
            with self.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT 1")
                return cur.fetchone()[0] == 1
        except Exception:
            return False

class Database:
    """Класс для работы с базой данных (PostgreSQL или SQLite)."""
    def __init__(self):
        if USE_POSTGRES:
            print("Using PostgreSQL database")
            self.db = PostgresDatabase()
        else:
            print("Using SQLite database")
            self.db = SQLiteDatabase()

    def save_game_result(self, user_id: int, game_data: dict):
        return self.db.save_game_result(user_id, game_data)

    def get_all_user_games(self, user_id: int) -> list:
        return self.db.get_all_user_games(user_id)

    def get_user_games_count(self, user_id: int) -> int:
        return self.db.get_user_games_count(user_id)

    def clear_user_stats(self, user_id: int) -> int:
        return self.db.clear_user_stats(user_id)

    def is_new_user(self, user_id: int) -> bool:
        return self.db.is_new_user(user_id)

    def register_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> bool:
        return self.db.register_user(user_id, username, first_name, last_name)

    def mark_user_notified(self, user_id: int):
        return self.db.mark_user_notified(user_id)

    def get_all_users(self) -> list:
        return self.db.get_all_users()

    def get_database_stats(self) -> dict:
        return self.db.get_database_stats()

    def test_connection(self) -> bool:
        return self.db.test_connection()

    def clear_all_data(self):
        if hasattr(self.db, "clear_all_data"):
            return self.db.clear_all_data()
        return None
