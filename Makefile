.PHONY: help up down logs run-local-sqlite run-local-pg webhook-delete

PYTHON ?= python3

help:
	@echo "  make run-local-sqlite  - polling + SQLite"
	@echo "  make up                - docker bot + postgres (polling)"
	@echo "  make down              - stop docker"
	@echo "  make webhook-delete    - delete Telegram webhook (back to polling)"

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f bot

run-local-sqlite:
	FORCE_SQLITE=true $(PYTHON) run_bot.py

run-local-pg:
	FORCE_SQLITE=false \
	USE_POSTGRES=true \
	PGHOST=localhost \
	PGPORT=5434 \
	PGDATABASE=scorer_db \
	PGUSER=scorer_user \
	PGPASSWORD=scorer_password \
	PGSSLMODE=disable \
	$(PYTHON) run_bot.py

webhook-delete:
	$(PYTHON) scripts/set_webhook.py --delete
