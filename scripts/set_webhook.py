#!/usr/bin/env python3
"""setWebhook / deleteWebhook для Telegram.

  python scripts/set_webhook.py
  python scripts/set_webhook.py --delete
"""
from __future__ import annotations

import argparse
import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--delete", action="store_true")
    parser.add_argument("--url", default=os.getenv("WEBHOOK_URL", ""))
    args = parser.parse_args()

    token = os.getenv("BOT_TOKEN")
    secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    if not token:
        print("BOT_TOKEN is missing", file=sys.stderr)
        sys.exit(1)

    if args.delete:
        r = httpx.post(f"https://api.telegram.org/bot{token}/deleteWebhook", timeout=20)
        print(r.json())
        return

    url = args.url.rstrip("/")
    if not url:
        print("WEBHOOK_URL is missing (https://<project>.vercel.app/telegram)", file=sys.stderr)
        sys.exit(1)

    r = httpx.post(
        f"https://api.telegram.org/bot{token}/setWebhook",
        data={
            "url": url,
            "secret_token": secret,
            "drop_pending_updates": "true",
        },
        timeout=20,
    )
    print(r.json())


if __name__ == "__main__":
    main()
