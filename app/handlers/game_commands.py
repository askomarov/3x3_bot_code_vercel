"""
Обработчики команд, связанных с игрой и турнирами
"""
import httpx
from telegram import Update
from telegram.ext import ContextTypes

from .base import BaseHandler
from ..utils import md2, md2_bold


class GameCommandHandlers(BaseHandler):
    """Обработчики игровых команд и поиска турниров"""

    async def serbia_tournaments_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Поиск турниров в Сербии"""
        try:
            self.log_user_action(update, "requested Serbia tournaments")

            await update.message.reply_text("🔍 search for Tournaments in Serbia...")

            # URL для API FIBA 3x3
            url = "https://play.fiba3x3.com/api/v2/search/events"
            params = {
                "countryIso2": "RS",
                "name": "",
                "input": "",
                "season": "",
                "when": "future",
                "distance": "100"
            }

            self.logger.info(f"🌐 Making API request to: {url}")
            self.logger.info(f"📋 Request parameters: {params}")

            # Заголовки для имитации браузера (обновленные)
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Referer": "https://play.fiba3x3.com/",
                "Origin": "https://play.fiba3x3.com",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"'
            }

            async with httpx.AsyncClient(headers=headers) as client:
                response = await client.get(url, params=params, timeout=10.0)

                if response.status_code == 200:
                    data = response.json()

                    # Форматируем ответ для пользователя
                    if data and isinstance(data, dict):
                        results = data.get('results', [])
                        if results:
                            message = (
                                md2_bold(
                                    f"🇷🇸 Upcoming tournaments in Serbia from the website "
                                    f"play.fiba3x3.com ({len(results)} найдено):"
                                )
                                + "\n\n"
                            )
                            for i, tournament in enumerate(results, 1):
                                tournament_id = tournament.get('id', '')
                                tournament_name = tournament.get('name', 'Empty name')

                                if tournament_id:
                                    message += f"{md2_bold(f'{i}.')} {md2(tournament_name)}\n"
                                    message += md2(
                                        f"https://play.fiba3x3.com/events/{tournament_id}"
                                    ) + "\n\n"
                        else:
                            message = md2("😔 no tournaments found")
                    else:
                        message = md2("📄 The data is received, but it is empty")

                    await update.message.reply_text(message, parse_mode='MarkdownV2')

                else:
                    self.logger.error(f"❌ API request failed with status {response.status_code}")
                    self.logger.error(f"❌ API response text: {response.text}")
                    await update.message.reply_text(f"❌ Ошибка при запросе данных: {response.status_code}")

        except httpx.TimeoutException:
            self.logger.error("⏰ Timeout while requesting Serbia tournaments")
            await update.message.reply_text("⏰ Превышено время ожидания ответа от сервера")
        except Exception as e:
            self.logger.error(f"❌ Error in serbia_tournaments_command: {e}")
            await update.message.reply_text("❌ Произошла ошибка при поиске турниров")
