# quantpilot-stock (apps/stock-assistant/backend)

Stock-assistant 后端：覆盖**人参与决策**的交易工作流——股票（Longbridge/FuTu）、期权、加密（OKX）、portfolio、screener、sentiment、结构化投顾，以及实盘前回测验证入口。

## 启动

```bash
# From repo root
./scripts/dev-stock.sh
# Or directly
cd apps/stock-assistant/backend
uv run uvicorn quantpilot_stock.main:app --port 8001 --reload
```

## 范围

**包含**：broker 接入、trading 引擎、broker 账户组合快照、screener、sentiment、agent 支撑的结构化投顾、options pricing、alerts、security/keyring、WebSocket。

**不包含**：本地模拟盘、自定义撮合、自动化量化研究（因子、ML 训练、无人值守策略运行）—— 这些不属于 stock-assistant 的赚钱闭环；回测计算由 `apps/quant-assistant/`（Rust）提供，stock-assistant 仅作为实盘前验证入口消费。

## 依赖

直接依赖 `quantpilot-common`（schemas 类型 + config + redis + data fetchers + platform contracts + strategy_persistence）。
