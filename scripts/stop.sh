#!/usr/bin/env bash
# JobFlow AI — stop all services started by deploy.sh

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDS="$ROOT/.pids"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[ok]${NC} $*"; }
warn() { echo -e "${YELLOW}[warn]${NC} $*"; }

stopped_any=0

if [[ -d "$PIDS" ]]; then
  for pidfile in "$PIDS"/*.pid; do
    [[ -e "$pidfile" ]] || continue
    name=$(basename "$pidfile" .pid)
    pid=$(cat "$pidfile" 2>/dev/null || echo "")
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      # Kill the whole process group (so child processes like next.js, celery workers go too)
      pkill -P "$pid" 2>/dev/null || true
      kill "$pid" 2>/dev/null || true
      sleep 0.5
      kill -9 "$pid" 2>/dev/null || true
      ok "stopped $name (pid $pid)"
      stopped_any=1
    fi
    rm -f "$pidfile"
  done
fi

# Belt-and-suspenders: kill anything still bound to our ports
for port in 3000 8000; do
  pids=$(lsof -ti :$port 2>/dev/null || true)
  if [[ -n "$pids" ]]; then
    echo "$pids" | xargs kill -9 2>/dev/null || true
    ok "killed remaining process on port $port"
    stopped_any=1
  fi
done

# Stop celery workers we may have spawned
pkill -f 'celery -A celery_worker' 2>/dev/null && { ok "stopped celery worker"; stopped_any=1; } || true

if [[ $stopped_any -eq 0 ]]; then
  warn "no JobFlow services were running"
fi

# Note: we leave redis-server running since it may serve other apps.
# To stop redis: redis-cli shutdown
