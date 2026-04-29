# Task F.21 — Form 4 内部人交易聚类信号 (Insider Trading Cluster Signal)

## 背景

基于 SEC EDGAR 免费 API（data.sec.gov）提取 Form 4 申报，
识别 90 天内多位高管/董事集群买入/卖出信号，剔除 10b5-1 自动计划单。

参考文献：Cohen, Malloy & Pomorski (2012) — 集群买入 180 日超额 6-10%。

## 范围（文件白名单）

```
apps/stock-assistant/backend/src/quantpilot_stock/insider_trading/__init__.py
apps/stock-assistant/backend/src/quantpilot_stock/insider_trading/engine.py
apps/stock-assistant/backend/src/quantpilot_stock/api/insider_trading.py
apps/stock-assistant/backend/src/quantpilot_stock/main.py
apps/stock-assistant/backend/tests/test_insider_trading.py
apps/stock-assistant/frontends/workbench/src/api/client.ts
apps/stock-assistant/frontends/workbench/src/components/InsiderTradingPanel.tsx
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx
docs/tasks/phaseF21/insider-trading.md
```

## 验收标准（AC）

### AC-1 数据模型

- `InsiderSignal` = Literal["cluster_buy","cluster_sell","mixed","neutral","no_data"]
- `InsiderTransaction` dataclass：insider_name, title, transaction_date, shares,
  price_per_share, transaction_type, is_10b5_plan, form_url
- `InsiderTradingData` dataclass：ticker, cik, signal, cluster_buy_count,
  cluster_sell_count, net_shares_90d, transactions, interpretation, as_of_date, data_available

### AC-2 信号逻辑

- 集群阈值：≥2 位不同内部人（distinct insiders）
- cluster_buy: buy_count ≥ 2 且 sell_count == 0
- cluster_sell: sell_count ≥ 2 且 buy_count == 0
- mixed: buy_count ≥ 2 且 sell_count ≥ 2
- neutral: 有交易但未达集群阈值
- no_data: 无任何合格交易

### AC-3 数据过滤

- 仅统计 90 天内（date.today() - 90 days）的 Form 4
- 10b5-1 计划单（is_10b5_plan=True）须剔除
- 仅计入 transaction_type in ("P", "S")（开放市场买入/卖出）

### AC-4 测试要求

- 测试总数 ≥ 16（实际 30）
- 覆盖：_compute_signal 所有分支
- 覆盖：_build_interpretation 各信号类型
- 覆盖：10b5-1 剔除逻辑
- 覆盖：90 天外交易排除
- 覆盖：CIK 未找到 → data_available=False
- 覆盖：EDGAR 异常 → data_available=False
- 覆盖：交易列表 cap at 20
- 所有测试 mock EDGAR 函数，不发真实网络请求

### AC-5 API

- 路由：`GET /api/insider-trading?ticker=<TICKER>`
- 无 ticker → HTTP 422
- 有 ticker → 始终 HTTP 200
- 通过 `include_with_api_alias(insider_trading_router)` 注册

### AC-6 前端

- `client.ts` 包含 InsiderSignal / InsiderTransactionItem / InsiderTradingData / fetchInsiderTrading
- `InsiderTradingPanel.tsx` 实现：
  - 信号 badge（颜色编码）
  - 买入/卖出内部人计数卡片
  - 净股份变动
  - 最近 10 条交易明细表
  - 降级提示 banner
- `RiskReviewCenter.tsx` 引入并渲染 `<InsiderTradingPanel />`
- TypeScript tsc --noEmit 通过
- Vite 生产构建通过

## 测试命令

```bash
cd apps/stock-assistant/backend && uv run pytest tests/test_insider_trading.py -v
```

## 静态检查

```bash
cd apps/stock-assistant/backend && uv run ruff check src/quantpilot_stock/insider_trading/ src/quantpilot_stock/api/insider_trading.py tests/test_insider_trading.py
cd apps/stock-assistant/backend && uv run mypy src/quantpilot_stock/insider_trading/ src/quantpilot_stock/api/insider_trading.py
```
