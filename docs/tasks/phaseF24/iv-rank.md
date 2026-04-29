# Task F.24 — 期权隐含波动率排名面板 (IV Rank & Volatility Monitor)

## 背景

衡量期权定价贵贱的核心指标：IV Rank（当前 IV 在过去一年范围内的百分位）和 IV Percentile
（过去一年中 IV 低于当前值的天数百分比）。IV Rank < 20 → 期权偏便宜，适合买入；
IV Rank > 80 → 期权偏贵，适合卖出。

同时显示历史波动率（HV10/20/30/60）、Put/Call Skew（下行保护偏好）以及期权期限结构。

数据来源：yfinance 期权链（免费）+ 价格历史

## 范围（文件白名单）

```
apps/stock-assistant/backend/src/quantpilot_stock/iv_rank/__init__.py
apps/stock-assistant/backend/src/quantpilot_stock/iv_rank/engine.py
apps/stock-assistant/backend/src/quantpilot_stock/api/iv_rank.py
apps/stock-assistant/backend/src/quantpilot_stock/main.py
apps/stock-assistant/backend/tests/test_iv_rank.py
apps/stock-assistant/frontends/workbench/src/api/client.ts
apps/stock-assistant/frontends/workbench/src/components/IVRankPanel.tsx
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx
docs/tasks/phaseF24/iv-rank.md
```

## 验收标准（AC）

### AC-1 数据模型

- `IVSignal` = Literal["buy_options","sell_options","neutral","no_data"]
- `TermStructurePoint` dataclass：expiry, days_to_expiry, atm_iv
- `IVRankData` dataclass：ticker, current_iv, iv_rank, iv_percentile,
  hv10, hv20, hv30, hv60, put_call_skew, term_structure, iv_signal,
  interpretation, as_of_date, data_available

### AC-2 计算逻辑

- HV = rolling log-return std × √252（窗口 10/20/30/60 天）
- 以 HV30 滚动序列作为历史 IV 代理
- IV Rank = (current_iv − min_52w) / (max_52w − min_52w) × 100，夹到 [0, 100]
- IV Percentile = 过去一年中 HV30 < current_iv 的天数百分比
- ATM IV = 最近期权链中离当前价最近的 call/put 隐含波动率均值
- Put/Call Skew = ATM put IV − ATM call IV（单位 pp）
- 信号：iv_rank < 20 → buy_options；> 80 → sell_options；其余 neutral

### AC-3 期权期限结构

- 抓取最多 5 个到期日（DTE ≥ 5）
- 每个到期日计算 ATM IV
- term_structure 按 DTE 升序排列

### AC-4 测试要求

- 测试总数 ≥ 16
- 覆盖：_compute_hv 正常 + 边界（窗口不足、常数价格）
- 覆盖：_get_atm_iv 正常 + 边界（仅 call、仅 put、空链）
- 覆盖：compute_iv_rank 正常（期权 + HV）、无期权降级（仅 HV）
- 覆盖：IV rank < 20 → buy_options；> 80 → sell_options
- 覆盖：yfinance 异常 → data_available=False
- 覆盖：历史不足 → data_available=False
- 覆盖：API GET /api/iv-rank，无 ticker 422，有 ticker 200
- 所有测试 mock 网络调用

### AC-5 API

- 路由：`GET /api/iv-rank?ticker=<TICKER>`
- 无 ticker → HTTP 422；有 ticker → 始终 200
- 通过 `include_with_api_alias(iv_rank_router)` 注册

### AC-6 前端

- `client.ts`：IVSignal / TermStructurePoint / IVRankData / fetchIVRank
- `IVRankPanel.tsx`：IV Rank 仪表盘 + HV 对比 + 期限结构表 + 信号徽章
- RiskReviewCenter.tsx 引入并渲染 `<IVRankPanel />`
- TypeScript tsc --noEmit 通过；Vite 构建通过

## 测试命令

```bash
cd apps/stock-assistant/backend && uv run pytest tests/test_iv_rank.py -v
```
