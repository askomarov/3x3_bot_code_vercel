"""
Утилиты для форматирования данных конкурса 3-х очковых бросков (3pts Contest)
"""
from .utils import number_to_emoji, format_time, md2, md2_bold


def format_contest_result(contest_data: dict) -> str:
    """Форматирование результата конкурса 3-х очковых для отправки (MarkdownV2)."""
    player_name = contest_data.get('playerName', 'Player')
    shots_attempted = contest_data.get('shotsAttempted', 0)
    shots_scored = contest_data.get('shotsScored', 0)
    max_shots = contest_data.get('maxShots', 25)
    percentage = contest_data.get('percentage', 0)
    game_time_total = contest_data.get('gameTimeTotal', 60)
    game_time_used = contest_data.get('gameTimeUsed', 0)
    game_time_remaining = contest_data.get('gameTimeRemaining', 0)

    shots_scored_emoji = number_to_emoji(shots_scored)
    shots_attempted_emoji = number_to_emoji(shots_attempted)
    percentage_emoji = number_to_emoji(percentage)

    if percentage >= 80:
        performance = md2("🔥 Excellent!")
    elif percentage >= 70:
        performance = md2("🎯 Great!")
    elif percentage >= 60:
        performance = md2("👍 Good!")
    elif percentage >= 50:
        performance = md2("👌 Not bad!")
    else:
        performance = md2("💪 Keep practicing!")

    pn = md2(player_name)
    tu = md2(format_time(game_time_used))
    tt = md2(format_time(game_time_total))
    tr = md2(format_time(game_time_remaining))

    result = "\n".join([
        "",
        md2_bold("🎯 3pts Contest finished!"),
        "",
        f"{md2_bold('Player:')} {pn}",
        "",
        md2_bold("Results:"),
        f"{md2('🏀 Scored:')} {shots_scored_emoji} / {shots_attempted_emoji}",
        f"{md2('🎯 Shots in round:')} {number_to_emoji(max_shots)}",
        f"{md2('📊 Accuracy:')} {percentage_emoji}{md2('%')}",
        performance,
        "",
        f"{md2('⏱ Time used:')} {tu} / {tt}",
        f"{md2('⏰ Time remaining:')} {tr}",
        "",
        md2("Great shooting! 🏆"),
        "",
    ])
    return result


def format_all_contests(contests: list) -> str:
    """Форматирование списка всех конкурсов с временными метками (MarkdownV2)."""
    if not contests:
        return md2("No saved contests")

    result = ""
    for i, contest in enumerate(contests, 1):
        player_name = contest.get('playerName', 'Player')
        shots_scored = contest.get('shotsScored', 0)
        shots_attempted = contest.get('shotsAttempted', 0)
        percentage = contest.get('percentage', 0)
        timestamp = contest.get('timestamp', '')

        shots_scored_emoji = number_to_emoji(shots_scored)
        shots_attempted_emoji = number_to_emoji(shots_attempted)
        percentage_emoji = number_to_emoji(percentage)

        if timestamp:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                date_str = dt.strftime('%d.%m.%Y %H:%M')
            except Exception:
                date_str = timestamp[:16].replace('T', ' ')
        else:
            date_str = "Unknown date"

        tail = md2(f"({percentage_emoji}%)")
        result += f"{md2_bold(f'{i}.')} {md2(date_str)}\n"
        result += f"   👤 {md2(player_name)}\n"
        result += f"   🎯 {shots_scored_emoji}/{shots_attempted_emoji} {tail}\n\n"

        if len(result) > 3500:
            remaining = len(contests) - i
            if remaining > 0:
                result += md2(f"... and {remaining} more contests") + "\n"
            break

    return result


def validate_contest_data(contest_data: dict) -> tuple[bool, str]:
    """Проверка корректности данных конкурса"""
    required_keys = [
        'playerName',
        'shotsAttempted',
        'shotsScored',
        'maxShots',
        'percentage',
        'gameTimeTotal',
        'gameTimeUsed',
        'gameTimeRemaining'
    ]

    # Проверка наличия всех необходимых ключей
    missing_keys = [key for key in required_keys if key not in contest_data]
    if missing_keys:
        return False, f"Missing keys: {missing_keys}"

    # Преобразование числовых полей
    try:
        contest_data['shotsAttempted'] = int(contest_data['shotsAttempted'])
        contest_data['shotsScored'] = int(contest_data['shotsScored'])
        contest_data['maxShots'] = int(contest_data['maxShots'])
        contest_data['percentage'] = int(contest_data['percentage'])
        contest_data['gameTimeTotal'] = int(contest_data['gameTimeTotal'])
        contest_data['gameTimeUsed'] = int(contest_data['gameTimeUsed'])
        contest_data['gameTimeRemaining'] = int(contest_data['gameTimeRemaining'])
    except (ValueError, TypeError):
        return False, "Invalid data types in contest data"

    # Проверка типов данных
    if not (isinstance(contest_data['playerName'], str) and
            isinstance(contest_data['shotsAttempted'], int) and
            isinstance(contest_data['shotsScored'], int) and
            isinstance(contest_data['maxShots'], int) and
            isinstance(contest_data['percentage'], int) and
            isinstance(contest_data['gameTimeTotal'], int) and
            isinstance(contest_data['gameTimeUsed'], int) and
            isinstance(contest_data['gameTimeRemaining'], int)):
        return False, "Invalid data types in contest data"

    # Проверка логических ограничений
    if contest_data['shotsScored'] > contest_data['shotsAttempted']:
        return False, "Shots scored cannot exceed shots attempted"

    if contest_data['percentage'] < 0 or contest_data['percentage'] > 100:
        return False, "Percentage must be between 0 and 100"

    return True, "OK"
