.PHONY: deploy stop status logs install dev backend frontend test migrate redis worker clean

# One-command deploy: installs deps, migrates, starts full stack in background
deploy:
	@bash scripts/deploy.sh

# Stop all services started by deploy
stop:
	@bash scripts/stop.sh

# Show status of running services
status:
	@echo "=== Service status ==="
	@for service in backend frontend worker redis; do \
		pidfile=.pids/$$service.pid; \
		if [ -f $$pidfile ] && kill -0 $$(cat $$pidfile) 2>/dev/null; then \
			echo "  ✓ $$service (pid $$(cat $$pidfile))"; \
		else \
			echo "  ✗ $$service"; \
		fi; \
	done
	@echo ""
	@echo "=== Ports ==="
	@lsof -i :3000 -i :8000 -i :6379 2>/dev/null | grep LISTEN || echo "  (no services listening)"

# Tail all logs
logs:
	@tail -f logs/backend.log logs/frontend.log logs/worker.log

# Manual targets (use `make deploy` for normal workflow)
install:
	cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
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
	cd backend && .venv/bin/celery -A celery_worker worker -l info

# Clean up logs and pid files
clean: stop
	rm -rf logs/*.log .pids/*.pid
