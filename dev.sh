#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
VENV="$BACKEND/.venv"
PID_FILE="$ROOT/.dev.pids"

kill_tree() {
  local pid="$1"
  local signal="${2:-TERM}"
  local child

  [[ -z "$pid" ]] && return 0
  kill -0 "$pid" 2>/dev/null || return 0

  while read -r child; do
    [[ -n "$child" ]] && kill_tree "$child" "$signal"
  done < <(pgrep -P "$pid" 2>/dev/null || true)

  kill "-$signal" "$pid" 2>/dev/null || kill "-$signal" -- "-$pid" 2>/dev/null || true
}

stop_dev() {
  if [[ -f "$PID_FILE" ]]; then
    # shellcheck disable=SC1090
    source "$PID_FILE"
    kill_tree "${BACKEND_PID:-}" TERM
    kill_tree "${FRONTEND_PID:-}" TERM
    sleep 0.5
    kill_tree "${BACKEND_PID:-}" KILL
    kill_tree "${FRONTEND_PID:-}" KILL
    rm -f "$PID_FILE"
  fi

# Fallback: anything still bound to our dev ports
  if command -v fuser >/dev/null 2>&1; then
    fuser -k -TERM 8000/tcp 5173/tcp 2>/dev/null || true
    sleep 0.3
    fuser -k -KILL 8000/tcp 5173/tcp 2>/dev/null || true
  fi
}

cleanup() {
  stop_dev
}
trap cleanup EXIT INT TERM

if [[ ! -d "$VENV" ]]; then
  echo "Creating Python venv..."
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q -r "$BACKEND/requirements.txt"
elif ! "$VENV/bin/python" -c "import fastapi" 2>/dev/null; then
  echo "Installing backend dependencies..."
  "$VENV/bin/pip" install -q -r "$BACKEND/requirements.txt"
fi

if [[ ! -d "$FRONTEND/node_modules" ]]; then
  echo "Installing frontend dependencies..."
  (cd "$FRONTEND" && npm install)
fi

# Clear any leftover processes from a prior run
stop_dev

echo "Starting backend  → http://127.0.0.1:8000"
setsid bash -c "cd '$BACKEND' && PYTHONPATH=. exec '$VENV/bin/uvicorn' app.main:app --reload --port 8000" &
BACKEND_PID=$!

echo "Starting frontend → http://localhost:5173"
setsid bash -c "cd '$FRONTEND' && exec npm run dev -- --host 127.0.0.1 --port 5173" &
FRONTEND_PID=$!

cat >"$PID_FILE" <<EOF
BACKEND_PID=$BACKEND_PID
FRONTEND_PID=$FRONTEND_PID
EOF

echo ""
echo "Whistle is running."
echo "  Stop both:  Ctrl+C in this terminal, or run ./dev-stop.sh"
echo "  Check ports: ss -tlnp | grep -E ':8000|:5173'"

wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
