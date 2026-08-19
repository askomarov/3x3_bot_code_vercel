"""
Утилиты для форматирования данных в 3x3 Scorer Bot
"""
import re
from urllib.parse import urlparse

# Совпадает с python-telegram-bot escape_markdown(..., version=2) без зависимости от пакета telegram.
_MD2_ESCAPE_CHARS = r"\_*[]()~`>#+-=|{}.!"


def md2(s: str) -> str:
    """Экранирование произвольного текста для Telegram MarkdownV2."""
    text = str(s)
    return re.sub(f"([{re.escape(_MD2_ESCAPE_CHARS)}])", r"\\\1", text)


def md2_bold(s: str) -> str:
    """Жирный текст MarkdownV2."""
    return f"*{md2(s)}*"


def number_to_emoji(number: int) -> str:
    """Преобразует число в строку с эмодзи цифр"""
    emoji_map = {
        '0': '0️⃣',
        '1': '1️⃣ ',
        '2': '2️⃣',
        '3': '3️⃣',
        '4': '4️⃣',
        '5': '5️⃣',
        '6': '6️⃣',
        '7': '7️⃣',
        '8': '8️⃣',
        '9': '9️⃣'
    }

    # Преобразуем число в строку и заменяем каждую цифру на эмодзи
    number_str = str(number)
    emoji_str = ''
    for digit in number_str:
        emoji_str += emoji_map.get(digit, digit)

    return emoji_str


def format_time(seconds: int) -> str:
    """Форматирование времени в ЧЧ:ММ:СС"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours > 0 else f"{minutes:02d}:{secs:02d}"


def format_game_result(game_data: dict) -> str:
    """Форматирование результата игры для отправки (MarkdownV2)."""
    score1 = game_data.get('score1', 0)
    score2 = game_data.get('score2', 0)
    team1_name = game_data.get('team1Name', 'Team 1')
    team2_name = game_data.get('team2Name', 'Team 2')
    winner = game_data.get('winner', 0)
    game_time = game_data.get('gameTime', 0)
    total_points = game_data.get('totalPoints', 0)
    fouls1 = game_data.get('fouls1', 0)
    fouls2 = game_data.get('fouls2', 0)

    score1_emoji = number_to_emoji(score1)
    score2_emoji = number_to_emoji(score2)
    total_points_emoji = number_to_emoji(total_points)
    fouls1_emoji = number_to_emoji(fouls1)
    fouls2_emoji = number_to_emoji(fouls2)

    t1 = md2(team1_name)
    t2 = md2(team2_name)
    dash = "\u2013"

    if winner == 1:
        winner_text = f"🏆 *{t1}* {md2('wins!')}"
    elif winner == 2:
        winner_text = f"🏆 *{t2}* {md2('wins!')}"
    else:
        winner_text = md2_bold("🤝 Draw!")

    time_s = md2(format_time(game_time))

    result = "\n".join([
        "",
        md2_bold("🏀 Game finished!"),
        "",
        f"*{t1}* {score1_emoji}  {dash}  {score2_emoji} *{t2}*",
        "",
        winner_text,
        "",
        f"{md2('⏱ Time:')} {time_s}",
        f"{md2('📊 Total points:')} {total_points_emoji}",
        f"🟨 {t1} {md2('-')} {fouls1_emoji} {md2('fouls')}",
        f"🟨 {t2} {md2('-')} {fouls2_emoji} {md2('fouls')}",
        "",
        md2("Great game! 🎉"),
        "",
    ])
    return result


def format_all_games(games: list) -> str:
    """Форматирование списка всех игр с временными метками (MarkdownV2)."""
    if not games:
        return md2("No saved games")

    result = ""
    dash = "\u2013"
    for i, game in enumerate(games, 1):
        score1 = game.get('score1', 0)
        score2 = game.get('score2', 0)
        team1_name = game.get('team1Name', 'Team 1')
        team2_name = game.get('team2Name', 'Team 2')
        winner = game.get('winner', 0)
        timestamp = game.get('timestamp', '')

        score1_emoji = number_to_emoji(score1)
        score2_emoji = number_to_emoji(score2)

        if winner == 1:
            winner_text = f"🏆 {md2(team1_name)}"
        elif winner == 2:
            winner_text = f"🏆 {md2(team2_name)}"
        else:
            winner_text = md2("🤝 Draw")

        if timestamp:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                date_str = dt.strftime('%d.%m.%Y %H:%M')
            except Exception:
                date_str = timestamp[:16].replace('T', ' ')
        else:
            date_str = "Unknown date"

        idx = md2_bold(f"{i}.")
        result += f"{idx} {md2(date_str)}\n"
        result += f"   {md2(team1_name)} {score1_emoji}  {dash}  {score2_emoji} {md2(team2_name)}\n"
        result += f"   {winner_text}\n\n"

        if len(result) > 3500:
            remaining = len(games) - i
            if remaining > 0:
                result += md2(f"... and {remaining} more games") + "\n"
            break

    return result


def is_valid_url(url):
    """Проверка корректности URL"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme == 'https'
    except ValueError:
        return False


def validate_game_data(game_data: dict) -> tuple[bool, str]:
    """Проверка корректности данных игры"""
    required_keys = ['score1', 'score2', 'team1Name', 'team2Name', 'winner', 'gameTime', 'totalPoints']

    # Проверка наличия всех необходимых ключей
    missing_keys = [key for key in required_keys if key not in game_data]
    if missing_keys:
        return False, f"Missing keys: {missing_keys}"

    # Преобразование числовых полей в целые числа
    try:
        game_data['score1'] = int(game_data['score1'])
        game_data['score2'] = int(game_data['score2'])
        game_data['winner'] = int(game_data['winner'])
        game_data['gameTime'] = int(game_data['gameTime'])
        game_data['totalPoints'] = int(game_data['totalPoints'])
        game_data['fouls1'] = int(game_data['fouls1'])
        game_data['fouls2'] = int(game_data['fouls2'])

    except (ValueError, TypeError):
        return False, "Invalid data types in game data"

    # Проверка типов данных
    if not (isinstance(game_data['score1'], int) and
            isinstance(game_data['score2'], int) and
            isinstance(game_data['team1Name'], str) and
            isinstance(game_data['team2Name'], str) and
            isinstance(game_data['winner'], int) and
            isinstance(game_data['gameTime'], int) and
            isinstance(game_data['totalPoints'], int)):
        return False, "Invalid data types in game data"

    return True, "OK"
