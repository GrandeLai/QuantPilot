#!/usr/bin/env bash
# Phase B 起：启动 Rust 量化助手全栈（backend 8002 axum + frontend 5175）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "[dev-quant] 启动基础设施..."
"$SCRIPT_DIR/infra.sh"

echo "[dev-quant] 启动 Rust quant-assistant 服务 (port 8002)..."
(cd "$ROOT_DIR" && cargo run --bin quantpilot-quant-server) &
PID_BACKEND=$!

echo "[dev-quant] 启动 quant 研究前端 (port 5175)..."
(cd "$ROOT_DIR/apps/quant-assistant/frontend" && QUANT_BACKEND=http://localhost:8002 npm run dev -- --port 5175 --strictPort) &
PID_FRONTEND=$!

trap 'echo "[dev-quant] stopping..."; kill $PID_BACKEND $PID_FRONTEND 2>/dev/null; exit 0' INT TERM

echo ""
echo "[dev-quant] All started. Open:"
echo "  - quant frontend: http://localhost:5175"
echo "  - API healthz:    http://localhost:8002/healthz"
echo ""
echo "[dev-quant] 提示：当前 Rust 后端仅 /healthz 端点；后续 task (phaseB.mvp.backtest) 加 /backtest"
echo ""

wait
