#!/usr/bin/env bash
# 首次安装脚本：安装所有依赖并构建 Rust 扩展
# 运行一次即可，后续用 dev.sh 启动
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

GREEN='\033[0;32m'
NC='\033[0m'
log() { echo -e "${GREEN}[setup]${NC} $*"; }

log "========================================"
log "  QuantPilot 初始化安装"
log "========================================"

# 1. 后端依赖
log "[1/3] 安装 Python 依赖..."
cd "$ROOT_DIR/backend"
uv sync --extra dev
log "Python 依赖安装完成 ✓"

# 2. Rust 扩展
log "[2/3] 构建 Rust 扩展（quantpilot_core）..."
uv run maturin develop --manifest-path ../rust_core/Cargo.toml
log "Rust 扩展构建完成 ✓"

# 3. 前端依赖
log "[3/3] 安装前端依赖..."
cd "$ROOT_DIR/frontend"
npm install
log "前端依赖安装完成 ✓"

echo ""
log "========================================"
log "  安装完成！"
log ""
log "  启动开发环境：  ./scripts/dev.sh"
log "  仅启动后端：    ./scripts/start_backend.sh"
log "  仅启动前端：    ./scripts/start_frontend.sh"
log "  仅启动 Redis：  ./scripts/infra.sh"
log "========================================"
