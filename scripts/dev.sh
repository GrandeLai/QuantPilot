#!/usr/bin/env bash
# QuantPilot 一键开发环境启动脚本
# 启动：Redis + 后端 API + 前端开发服务器
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[QuantPilot]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
info() { echo -e "${CYAN}[INFO]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

# 依赖检查
check_deps() {
    local missing=()
    command -v uv      &>/dev/null || missing+=("uv (brew install uv)")
    command -v cargo   &>/dev/null || missing+=("cargo (brew install rust)")
    command -v node    &>/dev/null || missing+=("node (brew install node)")
    command -v redis-cli &>/dev/null || missing+=("redis (brew install redis)")

    if [[ ${#missing[@]} -gt 0 ]]; then
        err "缺少依赖，请先安装：\n$(printf '  - %s\n' "${missing[@]}")"
    fi
}

# 加载 backend/.env（如果存在）
load_env() {
    local env_file="$ROOT_DIR/backend/.env"
    if [[ -f "$env_file" ]]; then
        while IFS='=' read -r key value; do
            [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
            # 只设置未在环境中显式指定的变量
            [[ -z "${!key+x}" ]] && export "$key=$value"
        done < "$env_file"
    fi
}

# 启动 Redis
start_redis() {
    local redis_url="${QUANTPILOT_REDIS_URL:-redis://localhost:6379}"

    # 远程 Redis：跳过本地启动
    if [[ "$redis_url" != "redis://localhost"* && "$redis_url" != "redis://:@localhost"* ]]; then
        info "使用远程 Redis: ${redis_url%%@*}@…（密码已隐藏）"
        return
    fi

    # 本地 Redis：确保已启动
    log "启动本地 Redis..."
    if redis-cli ping &>/dev/null 2>&1; then
        info "Redis 已在运行，跳过"
    else
        brew services start redis
        log "等待 Redis 就绪..."
        for i in {1..10}; do
            redis-cli ping &>/dev/null && break
            sleep 1
        done
        log "Redis 就绪 ✓  (redis://localhost:6379)"
    fi
}

# 安装后端依赖 & 构建 Rust 扩展
setup_backend() {
    log "安装后端依赖..."
    cd "$ROOT_DIR/backend"
    uv sync --extra dev

    log "构建 Rust 扩展（quantpilot_core）..."
    uv run maturin develop --manifest-path ../rust_core/Cargo.toml
    log "Rust 扩展构建完成 ✓"
}

# 安装前端依赖
setup_frontend() {
    log "安装前端依赖..."
    cd "$ROOT_DIR/frontend"
    if [[ ! -d node_modules ]]; then
        npm install
    else
        info "node_modules 已存在，跳过安装（如需更新请手动运行 npm install）"
    fi
}

# 启动后端（后台）
start_backend() {
    log "启动后端 API（http://localhost:8000）..."
    cd "$ROOT_DIR/backend"
    uv run uvicorn quantpilot.main:app \
        --host 127.0.0.1 \
        --port 8000 \
        --reload \
        --log-level info &
    BACKEND_PID=$!
    echo $BACKEND_PID > /tmp/quantpilot_backend.pid

    # 等待后端就绪
    for i in {1..15}; do
        curl -s http://localhost:8000/health &>/dev/null && break
        sleep 1
    done
    log "后端 API 就绪 ✓  (PID: $BACKEND_PID)"
}

# 启动前端（前台，阻塞）
start_frontend() {
    log "启动前端开发服务器（http://localhost:5173）..."
    cd "$ROOT_DIR/frontend"
    npm run dev
}

# 清理函数（Ctrl+C 时执行）
cleanup() {
    echo ""
    log "正在停止服务..."
    if [[ -f /tmp/quantpilot_backend.pid ]]; then
        kill "$(cat /tmp/quantpilot_backend.pid)" 2>/dev/null || true
        rm -f /tmp/quantpilot_backend.pid
    fi
    log "已停止。"
}
trap cleanup EXIT INT TERM

# ========== 主流程 ==========
echo ""
echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}     QuantPilot 开发环境启动                    ${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""

load_env
check_deps
start_redis
setup_backend
setup_frontend
start_backend
start_frontend
