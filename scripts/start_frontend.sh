#!/usr/bin/env bash
# 启动前端开发服务器（热更新，http://localhost:5173）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(dirname "$SCRIPT_DIR")/frontend"

if [[ ! -d node_modules ]]; then
    echo "[QuantPilot] 首次运行，安装前端依赖..."
    npm install
fi

echo "[QuantPilot] 启动前端开发服务器: http://localhost:5173"
exec npm run dev
