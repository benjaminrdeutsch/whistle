#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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

stopped=0

if [[ -f "$PID_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$PID_FILE"
  kill_tree "${BACKEND_PID:-}" TERM
  kill_tree "${FRONTEND_PID:-}" TERM
  sleep 0.5
  kill_tree "${BACKEND_PID:-}" KILL
  kill_tree "${FRONTEND_PID:-}" KILL
  rm -f "$PID_FILE"
  stopped=1
  echo "Stopped processes from $PID_FILE"
fi

if command -v fuser >/dev/null 2>&1; then
  if fuser 8000/tcp 5173/tcp >/dev/null 2>&1; then
    fuser -k -TERM 8000/tcp 5173/tcp 2>/dev/null || true
    sleep 0.3
    fuser -k -KILL 8000/tcp 5173/tcp 2>/dev/null || true
    stopped=1
    echo "Freed ports 8000 and 5173"
  fi
fi

if [[ "$stopped" -eq 0 ]]; then
  echo "No Whistle dev processes found."
else
  echo "Done. Verify with: ss -tlnp | grep -E ':8000|:5173' || echo 'ports clear'"
fi
