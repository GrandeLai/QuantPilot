#!/usr/bin/env bash
# Phase A 临时态：启动 Python 量化助手全栈（backend 8002 + frontend 5175）
# Step 4（Rust quant 对齐后）此脚本删除。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "[dev-quant-py] 启动基础设施..."
"$SCRIPT_DIR/infra.sh"

echo "[dev-quant-py] 启动 quant-py 后端 (port 8002)..."
(cd "$ROOT_DIR/apps/quant-assistant-py/backend" && uv run uvicorn quantpilot_quant.main:app --host 127.0.0.1 --port 8002 --reload) &
PID_BACKEND=$!

echo "[dev-quant-py] 启动 quant 研究前端 (port 5175)..."
(cd "$ROOT_DIR/apps/quant-assistant/frontend" && QUANT_BACKEND=http://localhost:8002 npm run dev -- --port 5175 --strictPort) &
PID_FRONTEND=$!

trap 'echo "[dev-quant-py] stopping..."; kill $PID_BACKEND $PID_FRONTEND 2>/dev/null; exit 0' INT TERM

echo ""
echo "[dev-quant-py] All started. Open:"
echo "  - quant frontend: http://localhost:5175"
echo "  - API docs:       http://localhost:8002/docs"
echo ""

wait
