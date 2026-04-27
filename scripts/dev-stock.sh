#!/usr/bin/env bash
# 启动股票助手全栈（backend 8001 + workbench 5173 + assistant 5174）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "[dev-stock] 启动基础设施..."
"$SCRIPT_DIR/infra.sh"

echo "[dev-stock] 启动 stock-assistant 后端 (port 8001)..."
(cd "$ROOT_DIR/apps/stock-assistant/backend" && uv run uvicorn quantpilot_stock.main:app --host 127.0.0.1 --port 8001 --reload) &
PID_BACKEND=$!

echo "[dev-stock] 启动 workbench 前端 (port 5173)..."
(cd "$ROOT_DIR/apps/stock-assistant/frontends/workbench" && npm run dev -- --port 5173 --strictPort) &
PID_WORKBENCH=$!

echo "[dev-stock] 启动 assistant 前端 (port 5174)..."
(cd "$ROOT_DIR/apps/stock-assistant/frontends/assistant" && npm run dev -- --port 5174 --strictPort) &
PID_ASSISTANT=$!

trap 'echo "[dev-stock] stopping..."; kill $PID_BACKEND $PID_WORKBENCH $PID_ASSISTANT 2>/dev/null; exit 0' INT TERM

echo ""
echo "[dev-stock] All started. Open:"
echo "  - workbench: http://localhost:5173"
echo "  - assistant: http://localhost:5174"
echo "  - API docs:  http://localhost:8001/docs"
echo ""

wait
