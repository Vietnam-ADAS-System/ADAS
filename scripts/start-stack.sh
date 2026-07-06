#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_CMD="${PYTHON:-python3}"
HOST="${HOST:-127.0.0.1}"
BACKEND_PORT="${PORT:-3000}"
AI_PORT="${AI_PORT:-8501}"
PIDS=()

cleanup() {
  trap - EXIT INT TERM
  if ((${#PIDS[@]})); then
    kill "${PIDS[@]}" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

cd "$ROOT_DIR"

unset NODE_OPTIONS

free_port() {
  local port="$1"
  local service="$2"
  local pids
  pids="$(lsof -nP -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"

  if [[ -z "$pids" ]]; then
    return
  fi

  for pid in $pids; do
    local command
    command="$(ps -p "$pid" -o command= 2>/dev/null || true)"

    if [[ "$command" == *"backend/node-server/realtime.js"* || "$command" == *"backend/node-server/stack-server.js"* || "$command" == *"backend/node-server/driver-server.js"* || "$command" == *"streamlit run main.py"* || "$command" == *"$ROOT_DIR"* ]]; then
      echo "[$service] stopping old ADAS process on port $port: $pid"
      kill "$pid" 2>/dev/null || true
    else
      echo "[$service] port $port is used by another process: $pid $command"
      echo "Stop it manually or change the port, then run npm run dev again."
      exit 1
    fi
  done

  sleep 1

  pids="$(lsof -nP -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    echo "[$service] port $port is still busy: $pids"
    exit 1
  fi
}

ensure_running() {
  local pid="$1"
  local service="$2"

  if ! kill -0 "$pid" 2>/dev/null; then
    echo "[$service] failed to start"
    exit 1
  fi
}

echo "Starting ADAS stack"
echo "MAIN DRIVER UI:     http://localhost:${BACKEND_PORT}/"
echo "Realtime backend:   http://${HOST}:${BACKEND_PORT}/api/health"
echo "Model test page:    http://localhost:${AI_PORT}/"
echo "Open MAIN DRIVER UI for the ADAS driving-assistance dashboard."

free_port "$BACKEND_PORT" "backend"
free_port "$AI_PORT" "ai"

BACKEND_ENTRY="backend/node-server/driver-server.js"

node --check "$BACKEND_ENTRY" >/dev/null

echo "[backend] starting"
HOST="$HOST" PORT="$BACKEND_PORT" node "$BACKEND_ENTRY" &
PIDS+=("$!")
sleep 2
ensure_running "${PIDS[0]}" "backend"

echo "[ai] starting"
"$PYTHON_CMD" -m streamlit run main.py \
  --server.address "$HOST" \
  --server.port "$AI_PORT" \
  --server.headless true \
  --browser.gatherUsageStats false &
PIDS+=("$!")
sleep 2
ensure_running "${PIDS[1]}" "ai"

wait
