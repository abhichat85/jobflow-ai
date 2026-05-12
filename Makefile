.PHONY: dev test backend frontend install

install:
	cd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt
	cd frontend && npm install

backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

dev:
	$(MAKE) -j2 backend frontend

test:
	cd backend && .venv/bin/pytest tests/ -v

migrate:
	cd backend && .venv/bin/alembic upgrade head

redis:
	redis-server

worker:
	cd backend && .venv/bin/celery -A app.celery_worker worker -l info
