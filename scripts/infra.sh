#!/usr/bin/env bash
# 启动基础设施（Redis），不含应用服务
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# 加载 .env（依次尝试 stock-assistant、quant-assistant-py、root）
for env_file in \
    "$ROOT_DIR/apps/stock-assistant/backend/.env" \
    "$ROOT_DIR/apps/quant-assistant-py/backend/.env" \
    "$ROOT_DIR/.env"; do
    if [[ -f "$env_file" ]]; then
        while IFS='=' read -r key value; do
            [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
            [[ -z "${!key+x}" ]] && export "$key=$value"
        done < "$env_file"
        break
    fi
done

REDIS_URL="${QUANTPILOT_REDIS_URL:-redis://localhost:6379}"

# 远程 Redis：只做连通性检查
if [[ "$REDIS_URL" != "redis://localhost"* && "$REDIS_URL" != "redis://:@localhost"* ]]; then
    echo "[QuantPilot] 使用远程 Redis，跳过本地启动"
    redis-cli -u "$REDIS_URL" ping && echo "[QuantPilot] 远程 Redis 连通 ✓" || echo "[WARN] 远程 Redis 不可达，请检查 QUANTPILOT_REDIS_URL"
    exit 0
fi

# 本地 Redis
command -v redis-cli &>/dev/null || { echo "[ERROR] 未找到 redis-cli，请先安装：brew install redis"; exit 1; }

echo "[QuantPilot] 启动本地 Redis..."
if redis-cli ping &>/dev/null 2>&1; then
    echo "[QuantPilot] Redis 已在运行 ✓"
else
    brew services start redis
    echo "[QuantPilot] 等待 Redis 就绪..."
    for i in {1..10}; do
        redis-cli ping &>/dev/null && break
        sleep 1
    done
    echo "[QuantPilot] Redis 就绪 ✓  (redis://localhost:6379)"
fi
