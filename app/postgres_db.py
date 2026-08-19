"""
PostgreSQL database handler для 3x3 Scorer Bot
"""
import psycopg2
import psycopg2.extras
import json
from urllib.parse import urlparse
from .config import DATABASE_URL, PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD, PGSSLMODE


class PostgresDatabase:
    """Класс для работы с PostgreSQL базой данных"""

    def __init__(self):
        self.connection_params = self._get_connection_params()
        self.setup_db()

    def _get_connection_params(self):
        """Получение параметров подключения к PostgreSQL"""
        # Railway обычно требует sslmode=require, локальный Postgres в Docker чаще работает с disable/prefer.
        ssl_mode = PGSSLMODE or ('require' if DATABASE_URL else 'prefer')

        if DATABASE_URL:
            # Парсим DATABASE_URL
            url = urlparse(DATABASE_URL)
            return {
                'host': url.hostname,
                'port': url.port or 5432,
                'database': url.path[1:],  # убираем первый слэш
                'user': url.username,
                'password': url.password,
                'sslmode': ssl_mode
            }
        else:
            # Используем отдельные переменные окружения
            return {
                'host': PGHOST,
                'port': int(PGPORT),
                'database': PGDATABASE,
                'user': PGUSER,
                'password': PGPASSWORD,
                'sslmode': ssl_mode
            }

    def get_connection(self):
        """Создает новое подключение к базе данных"""
        try:
            return psycopg2.connect(**self.connection_params)
        except Exception as e:
            print(f"Database connection error: {e}")
            raise

    def setup_db(self):
        """Инициализация PostgreSQL базы данных"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Создаем таблицу games
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS games (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT NOT NULL,
                            game_data JSONB NOT NULL,
                            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')

                    # Создаем индекс для user_id
                    cur.execute('''
                        CREATE INDEX IF NOT EXISTS idx_games_user_id ON games(user_id)
                    ''')

                    # Создаем индекс для timestamp
                    cur.execute('''
                        CREATE INDEX IF NOT EXISTS idx_games_timestamp ON games(timestamp DESC)
                    ''')

                    # Таблица для отслеживания пользователей
                    cur.execute('''
                        CREATE TABLE IF NOT EXISTS users (
                            user_id BIGINT PRIMARY KEY,
                            username VARCHAR(255),
                            first_name VARCHAR(255),
                            last_name VARCHAR(255),
                            first_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            is_notified BOOLEAN DEFAULT FALSE
                        )
                    ''')

                    # Индекс для сортировки пользователей
                    cur.execute('''
                        CREATE INDEX IF NOT EXISTS idx_users_first_seen ON users(first_seen DESC)
                    ''')

                conn.commit()
                print("PostgreSQL database initialized successfully")
        except Exception as e:
            print(f"Database initialization error: {e}")
            raise

    def save_game_result(self, user_id: int, game_data: dict):
        """Сохранение результата игры в базу данных"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'INSERT INTO games (user_id, game_data) VALUES (%s, %s) RETURNING id',
                        (user_id, json.dumps(game_data, ensure_ascii=False))
                    )
                    game_id = cur.fetchone()[0]
                conn.commit()
                print(f"✅ PostgreSQL: Game saved successfully (ID: {game_id}, User: {user_id})")
        except Exception as e:
            print(f"❌ PostgreSQL: Failed to save game result: {e}")
            raise

    def get_all_user_games(self, user_id: int) -> list:
        """Получение всех игр пользователя"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        'SELECT game_data, timestamp FROM games WHERE user_id = %s ORDER BY timestamp DESC',
                        (user_id,)
                    )
                    games = []
                    for row in cur.fetchall():
                        game_data = row['game_data']
                        if isinstance(game_data, str):
                            game_data = json.loads(game_data)
                        game_data['timestamp'] = row['timestamp'].isoformat()
                        games.append(game_data)
                    return games
        except Exception as e:
            print(f"Failed to get all user games: {e}")
            return []

    def get_user_games_count(self, user_id: int) -> int:
        """Получение количества игр пользователя"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('SELECT COUNT(*) FROM games WHERE user_id = %s', (user_id,))
                    return cur.fetchone()[0]
        except Exception as e:
            print(f"Failed to get user games count: {e}")
            return 0

    def clear_user_stats(self, user_id: int) -> int:
        """Очистка статистики пользователя"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('SELECT COUNT(*) FROM games WHERE user_id = %s', (user_id,))
                    count = cur.fetchone()[0]
                    cur.execute('DELETE FROM games WHERE user_id = %s', (user_id,))
                conn.commit()
                return count
        except Exception as e:
            print(f"Failed to clear user stats: {e}")
            return 0

    def is_new_user(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь новым"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('SELECT user_id FROM users WHERE user_id = %s', (user_id,))
                    return cur.fetchone() is None
        except Exception as e:
            print(f"Failed to check if user is new: {e}")
            return False

    def register_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> bool:
        """Регистрирует нового пользователя"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('''
                        INSERT INTO users (user_id, username, first_name, last_name, is_notified)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (user_id) DO UPDATE SET
                            username = EXCLUDED.username,
                            first_name = EXCLUDED.first_name,
                            last_name = EXCLUDED.last_name,
                            is_notified = FALSE
                        RETURNING user_id, (xmax = 0) as is_new_user
                    ''', (user_id, username, first_name, last_name, False))
                    result = cur.fetchone()
                    is_new = result[1] if result else False
                conn.commit()
                print(f"✅ PostgreSQL: User {'registered' if is_new else 'updated'} (ID: {user_id}, Username: {username})")
                return True
        except Exception as e:
            print(f"❌ PostgreSQL: Failed to register user: {e}")
            return False

    def mark_user_notified(self, user_id: int):
        """Отмечает, что админ был уведомлен о пользователе"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('UPDATE users SET is_notified = %s WHERE user_id = %s', (True, user_id))
                conn.commit()
        except Exception as e:
            print(f"Failed to mark user as notified: {e}")

    def get_all_users(self) -> list:
        """Получает список всех пользователей"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute('''
                        SELECT user_id, username, first_name, last_name, first_seen
                        FROM users
                        ORDER BY first_seen DESC
                    ''')
                    users = []
                    for row in cur.fetchall():
                        users.append({
                            'user_id': row['user_id'],
                            'username': row['username'],
                            'first_name': row['first_name'],
                            'last_name': row['last_name'],
                            'first_seen': row['first_seen'].isoformat() if row['first_seen'] else None
                        })
                    return users
        except Exception as e:
            print(f"Failed to get all users: {e}")
            return []

    def get_database_stats(self) -> dict:
        """Получает статистику базы данных"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Общее количество пользователей
                    cur.execute('SELECT COUNT(*) FROM users')
                    total_users = cur.fetchone()[0]

                    # Общее количество игр
                    cur.execute('SELECT COUNT(*) FROM games')
                    total_games = cur.fetchone()[0]

                    # Последние 5 игр
                    cur.execute('''
                        SELECT user_id, timestamp
                        FROM games
                        ORDER BY timestamp DESC
                        LIMIT 5
                    ''')
                    recent_games = [
                        {'user_id': row[0], 'timestamp': row[1].isoformat()}
                        for row in cur.fetchall()
                    ]

                    # Версия PostgreSQL
                    cur.execute('SELECT version()')
                    pg_version = cur.fetchone()[0]

                    return {
                        'database_type': 'PostgreSQL',
                        'total_users': total_users,
                        'total_games': total_games,
                        'recent_games': recent_games,
                        'pg_version': pg_version.split(',')[0]  # Только основная версия
                    }
        except Exception as e:
            print(f"Failed to get database stats: {e}")
            return {'error': str(e)}

    def test_connection(self) -> bool:
        """Тестирует подключение к базе данных"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('SELECT 1')
                    result = cur.fetchone()[0]
                    print(f"✅ PostgreSQL connection test successful: {result}")
                    return True
        except Exception as e:
            print(f"❌ PostgreSQL connection test failed: {e}")
            return False

    def clear_all_data(self):
        """Полная очистка таблиц users и games."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('DELETE FROM games')
                    cur.execute('DELETE FROM users')
                conn.commit()
        except Exception as e:
            print(f"Failed to clear all PostgreSQL data: {e}")
            raise
