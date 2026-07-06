#!/usr/bin/env bash
set -euo pipefail

# ADAS Full Stack Start Script
# Chạy: bash scripts/start-all.sh
# Hoặc: ./scripts/start-all.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_CMD="${PYTHON:-python3}"
NODE_CMD="${NODE:-node}"

HOST="${HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-3000}"
AI_PORT="${AI_PORT:-8765}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

PIDS=()

cleanup() {
  trap - EXIT INT TERM
  if ((${#PIDS[@]})); then
    echo ""
    echo "Stopping all services..."
    for pid in "${PIDS[@]}"; do
      kill "$pid" 2>/dev/null || true
    done
  fi
}

trap cleanup EXIT INT TERM

cd "$ROOT_DIR"

echo "========================================"
echo "  ADAS FULL STACK - Starting..."
echo "========================================"
echo ""

# Check ports
check_port() {
  local port=$1
  local name=$2
  if lsof -nP -iTCP:$port -sTCP:LISTEN >/dev/null 2>&1; then
    echo "⚠️  Port $port ($name) is already in use"
  else
    echo "✓ Port $port ($name) is free"
  fi
}

echo "Checking ports..."
check_port $BACKEND_PORT "Node Server"
check_port $AI_PORT "AI WebSocket"
check_port $FRONTEND_PORT "Frontend"
echo ""

# 1. Start Node.js Backend Server
echo "[1/3] Starting Node.js Backend Server..."
HOST=$HOST PORT=$BACKEND_PORT node "$ROOT_DIR/backend/node-server/server.js" &
PIDS+=("$!")
sleep 2

if ! kill -0 "${PIDS[0]}" 2>/dev/null; then
  echo "❌ Failed to start Node.js server"
  exit 1
fi
echo "✓ Node.js server running at http://$HOST:$BACKEND_PORT"
echo ""

# 2. Start AI Backend (Python)
echo "[2/3] Starting AI Backend (Python)..."
cd "$ROOT_DIR/backend/ai-service"

# Activate venv if exists
if [ -d "venv" ]; then
  echo "  (Using virtual environment)"
fi

$PYTHON_CMD run_unified.py --webcam --fps 15 &
PIDS+=("$!")
sleep 3

if ! kill -0 "${PIDS[1]}" 2>/dev/null; then
  echo "⚠️  AI backend may have issues, but continuing..."
fi
echo "✓ AI backend running on port $AI_PORT"
echo ""

# 3. Start Frontend
echo "[3/3] Starting Frontend..."
cd "$ROOT_DIR/frontend"
npm run dev &
PIDS+=("$!")
sleep 3

if ! kill -0 "${PIDS[2]}" 2>/dev/null; then
  echo "❌ Failed to start Frontend"
  exit 1
fi
echo "✓ Frontend running at http://localhost:$FRONTEND_PORT"
echo ""

echo "========================================"
echo "  ADAS FULL STACK - RUNNING"
echo "========================================"
echo ""
echo "  Dashboard:    http://localhost:$FRONTEND_PORT"
echo "  Node API:     http://$HOST:$BACKEND_PORT/api/health"
echo "  AI WebSocket: ws://$HOST:$AI_PORT"
echo ""
echo "  Press Ctrl+C to stop all services"
echo "========================================"
echo ""

# Wait for all processes
wait
