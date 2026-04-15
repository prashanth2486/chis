source venv/bin/activate#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PID_DIR="$ROOT_DIR/.demo_pids"

stop_pid() {
  local name="$1"
  local file="$2"
  if [[ -f "$file" ]]; then
    local pid
    pid="$(cat "$file")"
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
      echo "Stopped $name (PID $pid)"
    else
      echo "$name process already stopped (PID $pid)"
    fi
    rm -f "$file"
  fi
}

stop_pid "backend" "$PID_DIR/backend.pid"
stop_pid "frontend" "$PID_DIR/frontend.pid"

echo "Demo services cleanup complete"
