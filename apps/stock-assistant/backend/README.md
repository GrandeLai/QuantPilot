# quantpilot-stock (apps/stock-assistant/backend)

Stock-assistant 后端：覆盖**人参与决策**的交易工作流——股票（Longbridge/FuTu）、期权、加密（OKX）、portfolio、screener、sentiment、结构化投顾。

## 启动

```bash
# From repo root
./scripts/dev-stock.sh
# Or directly
cd apps/stock-assistant/backend
uv run uvicorn quantpilot_stock.main:app --port 8001 --reload
```

## 范围

**包含**：broker 接入、trading 引擎、paper trading、portfolio 管理、screener、sentiment、agent 支撑的结构化投顾、options pricing、alerts、security/keyring、WebSocket。

**不包含**：自动化量化研究（回测、因子、ML、信号、策略生成）—— 这些在 `apps/quant-assistant-py/`（Phase A）→ `apps/quant-assistant/`（Rust，Phase B+）。

## 依赖

直接依赖 `quantpilot-common`（schemas 类型 + config + redis + data fetchers + platform contracts + strategy_persistence）。
