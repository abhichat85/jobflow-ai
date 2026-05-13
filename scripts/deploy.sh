#!/usr/bin/env bash
# JobFlow AI — one-command deploy
# Sets up dependencies, runs migrations, starts the full stack in background.
# Idempotent: safe to run repeatedly.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LOGS="$ROOT/logs"
PIDS="$ROOT/.pids"
mkdir -p "$LOGS" "$PIDS"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${BLUE}[deploy]${NC} $*"; }
ok()   { echo -e "${GREEN}[ok]${NC} $*"; }
warn() { echo -e "${YELLOW}[warn]${NC} $*"; }
err()  { echo -e "${RED}[err]${NC} $*" >&2; }

# ---------- Prerequisite checks ----------
log "Checking prerequisites..."

command -v python3 >/dev/null || { err "python3 not found"; exit 1; }
command -v node >/dev/null || { err "node not found"; exit 1; }
command -v npm >/dev/null || { err "npm not found"; exit 1; }

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
NODE_VERSION=$(node -v | sed 's/v//')
ok "python3 $PY_VERSION, node $NODE_VERSION"

if ! command -v redis-server >/dev/null; then
  warn "redis-server not found in PATH"
  if [[ "$(uname)" == "Darwin" ]]; then
    err "Install with: brew install redis"
  else
    err "Install with: sudo apt install redis-server"
  fi
  exit 1
fi
ok "redis-server present"

# ---------- Environment ----------
if [[ ! -f .env ]]; then
  log "Creating .env from .env.example"
  cp .env.example .env
  warn "Edit .env and set ANTHROPIC_API_KEY before re-running"
  echo "  $ROOT/.env"
  exit 1
fi

# Validate ANTHROPIC_API_KEY is set
if grep -q '^ANTHROPIC_API_KEY=sk-ant-\.\.\.$' .env || grep -q '^ANTHROPIC_API_KEY=$' .env; then
  err "ANTHROPIC_API_KEY in .env is not set. Edit $ROOT/.env"
  exit 1
fi
ok ".env present and configured"

# ---------- Backend setup ----------
log "Setting up backend..."
cd "$ROOT/backend"

if [[ ! -d .venv ]]; then
  log "Creating Python venv"
  python3 -m venv .venv
fi

# Always ensure deps are current
log "Installing backend dependencies"
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
ok "Backend dependencies ready"

log "Ensuring Playwright Chromium is installed"
if ! .venv/bin/playwright install --dry-run chromium 2>/dev/null | grep -q "already installed"; then
  .venv/bin/playwright install chromium
fi
ok "Playwright Chromium ready"

# Ensure data directories exist
mkdir -p data/db data/resumes data/templates

log "Running database migrations"
.venv/bin/alembic upgrade head
ok "Database migrated"

cd "$ROOT"

# ---------- Frontend setup ----------
log "Setting up frontend..."
cd "$ROOT/frontend"

if [[ ! -d node_modules ]]; then
  log "Installing frontend dependencies (first run)"
  npm install --silent
else
  log "Frontend dependencies present (skipping install)"
fi
ok "Frontend ready"

cd "$ROOT"

# ---------- Stop any existing services ----------
log "Stopping any existing JobFlow services..."
"$ROOT/scripts/stop.sh" >/dev/null 2>&1 || true

# ---------- Start services ----------
start_bg() {
  local name=$1
  local cmd=$2
  local logfile="$LOGS/$name.log"
  local pidfile="$PIDS/$name.pid"

  log "Starting $name → $logfile"
  # Unset any inherited empty-string secrets so pydantic_settings reads them from .env.
  # (Some parent shells — including Claude Code's — export these as empty.)
  # shellcheck disable=SC2086
  ( cd "$ROOT" \
    && unset ANTHROPIC_API_KEY FIRECRAWL_API_KEY TAVILY_API_KEY \
    && nohup bash -c "$cmd" > "$logfile" 2>&1 & echo $! > "$pidfile" )
  sleep 1
  if kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    ok "$name started (pid $(cat "$pidfile"))"
  else
    err "$name failed to start — check $logfile"
    tail -n 20 "$logfile" >&2 || true
    return 1
  fi
}

# Redis (only start if not already running)
if pgrep -x redis-server >/dev/null; then
  ok "redis already running"
else
  start_bg redis "redis-server --port 6379"
fi

start_bg backend "cd backend && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000"
start_bg worker  "cd backend && .venv/bin/celery -A celery_worker worker -l info"
start_bg frontend "cd frontend && npm run dev"

# ---------- Health checks ----------
log "Waiting for services to come online..."

wait_for() {
  local url=$1 label=$2 max=${3:-30}
  local i=0
  while (( i < max )); do
    if curl -sf -o /dev/null "$url"; then
      ok "$label responding at $url"
      return 0
    fi
    sleep 1
    ((i++))
  done
  err "$label did not respond at $url within ${max}s"
  return 1
}

wait_for "http://localhost:8000/api/health" backend 30 || {
  err "Backend failed. Last 30 lines of log:"
  tail -n 30 "$LOGS/backend.log" >&2
  exit 1
}

wait_for "http://localhost:3000" frontend 60 || {
  err "Frontend failed. Last 30 lines of log:"
  tail -n 30 "$LOGS/frontend.log" >&2
  exit 1
}

# ---------- Done ----------
echo
ok "JobFlow AI is live"
echo
echo "  Frontend:    http://localhost:3000"
echo "  Backend:     http://localhost:8000"
echo "  API docs:    http://localhost:8000/docs"
echo
echo "Logs:"
echo "  tail -f $LOGS/backend.log"
echo "  tail -f $LOGS/frontend.log"
echo "  tail -f $LOGS/worker.log"
echo
echo "Stop everything: make stop"
echo
echo "First-time setup: visit http://localhost:3000/profile/ingest to populate your profile."
