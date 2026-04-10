#!/usr/bin/env bash
# 启动后端 API 服务（需先运行 scripts/infra.sh 启动 Redis）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(dirname "$SCRIPT_DIR")/backend"

RELOAD=${RELOAD:-"--reload"}
HOST=${HOST:-"127.0.0.1"}
PORT=${PORT:-"8000"}

echo "[QuantPilot] 启动后端 API: http://${HOST}:${PORT}"
echo "[QuantPilot] API 文档: http://${HOST}:${PORT}/docs"
echo ""

exec uv run uvicorn quantpilot.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --log-level info \
    $RELOAD
