# 3x3 Scorer Bot (без новостей) — Vercel webhook

Копия основного бота: счёт, Mini Apps, админка, Postgres/SQLite. Без парсинга FIBA, OpenAI и JobQueue.

Локально — polling (`run_bot.py`). На Vercel — webhook (`main.py`).

**Не используй тот же `BOT_TOKEN`, что у основного бота.** Webhook и polling на одном токене не живут вместе.

## Что выкинуто

- `app/scraping/`, `app/ai/`, `app/news_auto.py`, `app/news_state.py`
- кнопки Get News / Get News Rus
- автопубликация в каналы

## Локально (polling)

```bash
cp .env.example .env
# заполни BOT_TOKEN, WEBAPP_*, ADMIN_ID
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
FORCE_SQLITE=true python3 run_bot.py
```

## Vercel

Нужен Postgres снаружи (Neon / Supabase). SQLite на Vercel не живёт.

1. Репо в GitHub, `vercel` import, root = этот каталог.
2. Env в Vercel:
   - `BOT_TOKEN`
   - `WEBAPP_URL`, `WEBAPP_3PTS_URL`, `WEBAPP_TACTICAL_BOARD_URL`
   - `ADMIN_ID`
   - `DATABASE_URL` (Neon, `sslmode=require`)
   - `TELEGRAM_WEBHOOK_SECRET` (любая длинная строка)
   - `WEBHOOK_URL=https://<project>.vercel.app/telegram`
3. Deploy.
4. Повесь webhook (один раз):

```bash
# из этого каталога, с теми же env
python3 scripts/set_webhook.py

# или в браузере:
# https://<project>.vercel.app/setup-webhook?secret=<TELEGRAM_WEBHOOK_SECRET>
```

Проверка: `GET https://<project>.vercel.app/` → `{"ok": true}`.

Снять webhook (вернуть polling):

```bash
python3 scripts/set_webhook.py --delete
```

Hobby: функция до 30s, без cron — для этого бота достаточно.
