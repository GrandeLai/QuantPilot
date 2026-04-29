# Task F.23 — 指数调仓机会面板 (Index Rebalance Preview)

## 背景

检测股票是否在 S&P 500、NASDAQ 100、Russell 2000 中，并根据市值阈值评估
纳入/剔除风险。可预测 ETF 被动资金流向，提前布局指数调仓超额收益。

参考：Chen, Noronha & Singal (2004) — S&P 500 纳入前 1 个月平均超额 +8%。

数据来源：Wikipedia 成分股列表（免费）+ yfinance 市值

## 范围（文件白名单）

```
apps/stock-assistant/backend/src/quantpilot_stock/index_rebalance/__init__.py
apps/stock-assistant/backend/src/quantpilot_stock/index_rebalance/engine.py
apps/stock-assistant/backend/src/quantpilot_stock/api/index_rebalance.py
apps/stock-assistant/backend/src/quantpilot_stock/main.py
apps/stock-assistant/backend/tests/test_index_rebalance.py
apps/stock-assistant/frontends/workbench/src/api/client.ts
apps/stock-assistant/frontends/workbench/src/components/IndexRebalancePanel.tsx
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx
docs/tasks/phaseF23/index-rebalance.md
```

## 验收标准（AC）

### AC-1 数据模型

- `IndexStatus` = Literal["member","non_member","unknown"]
- `RebalanceRisk` = Literal["high_addition_risk","moderate_addition_risk","stable","moderate_deletion_risk","high_deletion_risk","unknown"]
- `IndexMembership` dataclass：index_name, status, market_cap_rank, market_cap_pct, rebalance_risk
- `IndexRebalanceData` dataclass：ticker, market_cap, market_cap_b, float_shares, price, eps_ttm,
  indices, interpretation, as_of_date, data_available

### AC-2 风险评估逻辑

- S&P 500：member 且 cap < $10B → high_deletion; non_member 且 cap > 1.5× min → high_addition
- NASDAQ 100：member 且 cap < 0.8× min → high_deletion; non_member 且 cap > 2× min → high_addition
- Russell 2000：按市值范围 [$300M, $3.5B] 估算成员身份

### AC-3 指数成员检测

- S&P 500：从 Wikipedia List_of_S&P_500_companies 表格读取
- NASDAQ 100：从 Wikipedia Nasdaq-100 表格读取
- Russell 2000：基于市值范围规则估算

### AC-4 测试要求

- 测试总数 ≥ 16（实际 35）
- 覆盖：_assess_sp500_risk 所有边界
- 覆盖：_assess_nq100_risk 所有边界
- 覆盖：_assess_russell_risk
- 覆盖：成员/非成员检测（mocked Wikipedia + yfinance）
- 覆盖：yfinance 异常 → data_available=False
- 覆盖：空 info → data_available=False
- 覆盖：API GET /api/index-rebalance，无 ticker 422，有 ticker 200
- 所有测试 mock 网络调用

### AC-5 API

- 路由：`GET /api/index-rebalance?ticker=<TICKER>`
- 无 ticker → HTTP 422；有 ticker → 始终 200
- 通过 `include_with_api_alias(index_rebalance_router)` 注册

### AC-6 前端

- `client.ts`：IndexStatus / RebalanceRisk / IndexMembershipItem / IndexRebalanceData / fetchIndexRebalance
- `IndexRebalancePanel.tsx`：市值信息卡 + 三指数成分行（状态 + 风险标签）+ 调仓机会计数
- RiskReviewCenter.tsx 引入并渲染 `<IndexRebalancePanel />`
- TypeScript tsc --noEmit 通过；Vite 构建通过

## 测试命令

```bash
cd apps/stock-assistant/backend && uv run pytest tests/test_index_rebalance.py -v
```
