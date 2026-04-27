#!/usr/bin/env bash
# Phase B 起：启动 Rust 量化助手全栈（backend 8002 + frontend 5175）
# 当前为占位脚本——Phase A 的 Rust seed 仅 PyO3 cdylib，未真正 axum 服务。
# Phase B MVP 时 cargo run 会启动 axum healthz + backtest 端点。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "[dev-quant] Phase A 占位——Rust quant-assistant 在 Phase B 才真正 serve"
echo "[dev-quant] 当前可跑：cargo check 验证 PyO3 seed crate 编译"
echo ""

echo "[dev-quant] cargo check apps/quant-assistant/backend..."
(cd "$ROOT_DIR/apps/quant-assistant/backend" && cargo check)

echo ""
echo "[dev-quant] 启动量化研究前端 skeleton (port 5175)..."
(cd "$ROOT_DIR/apps/quant-assistant/frontend" && QUANT_BACKEND=http://localhost:8002 npm run dev -- --port 5175 --strictPort) &
PID_FRONTEND=$!

trap 'echo "[dev-quant] stopping..."; kill $PID_FRONTEND 2>/dev/null; exit 0' INT TERM

echo ""
echo "[dev-quant] Phase A 提示：要让前端有数据，请同时跑 ./scripts/dev-quant-py.sh"
echo "[dev-quant] Phase B 时此脚本将启动 cargo run --release 替代上面的 quant-py 后端"
echo ""

wait
