#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_DIR="$ROOT_DIR/.demo_logs"
PID_DIR="$ROOT_DIR/.demo_pids"

mkdir -p "$LOG_DIR" "$PID_DIR"

if [[ -f "$PID_DIR/backend.pid" ]] || [[ -f "$PID_DIR/frontend.pid" ]]; then
  echo "Demo appears to be already running. Use ./scripts/stop_demo.sh first."
  exit 1
fi

BACKEND_CMD=("$BACKEND_DIR/venv/bin/python" -m uvicorn main:app --host 127.0.0.1 --port 8000)
FRONTEND_CMD=("$FRONTEND_DIR/venv/bin/python" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.baseUrlPath=)

(
  cd "$BACKEND_DIR"
  "${BACKEND_CMD[@]}" > "$LOG_DIR/backend.log" 2>&1 &
  echo $! > "$PID_DIR/backend.pid"
)

(
  cd "$FRONTEND_DIR"
  "${FRONTEND_CMD[@]}" > "$LOG_DIR/frontend.log" 2>&1 &
  echo $! > "$PID_DIR/frontend.pid"
)

sleep 1

echo "Demo services started"
echo "Backend : http://127.0.0.1:8000"
echo "Frontend: http://127.0.0.1:8501"
echo "API docs: http://127.0.0.1:8000/docs"
echo "Admin   : admin / admin123"
echo "Logs    : $LOG_DIR"
echo "Stop    : ./scripts/stop_demo.sh"
