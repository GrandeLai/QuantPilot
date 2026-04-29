# Task F.25 — 财报日历与期权预期波动面板 (Earnings Calendar & Expected Move)

## 背景

在财报公布前，用当前 ATM 跨式组合（Straddle）的价格估算市场隐含的预期波动幅度，
并与过去 8 次财报的实际股价波动对比，判断期权当前定价是偏贵还是偏便宜，
给出买入/卖出 Straddle 的参考信号。

参考：Option-implied earnings moves historically overestimate actual moves ~70% of time
（暗示系统性卖出 Straddle 有正期望值来源）。

数据来源：yfinance 期权链 + 价格历史 + 财报日历

## 范围（文件白名单）

```
apps/stock-assistant/backend/src/quantpilot_stock/earnings_calendar/__init__.py
apps/stock-assistant/backend/src/quantpilot_stock/earnings_calendar/engine.py
apps/stock-assistant/backend/src/quantpilot_stock/api/earnings_calendar.py
apps/stock-assistant/backend/src/quantpilot_stock/main.py
apps/stock-assistant/backend/tests/test_earnings_calendar.py
apps/stock-assistant/frontends/workbench/src/api/client.ts
apps/stock-assistant/frontends/workbench/src/components/EarningsCalendarPanel.tsx
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx
docs/tasks/phaseF25/earnings-calendar.md
```

## 验收标准（AC）

### AC-1 数据模型

- `StraddleSignal` = Literal["buy_straddle","sell_straddle","fair","unknown"]
- `EarningsMove` dataclass：date, actual_move_pct, beat_estimate (bool | None)
- `EarningsCalendarData` dataclass：ticker, next_earnings_date, days_to_earnings,
  implied_move_pct, historical_avg_move_pct, historical_moves, straddle_signal,
  interpretation, as_of_date, data_available

### AC-2 计算逻辑

- ATM Straddle 成本 = (ATM call lastPrice + ATM put lastPrice) / spot × 100（%）
- 最近到期日：取财报日后的首个期权到期日（DTE ≥ 1）
- 历史实际波动 = 财报日后首个交易日 vs 财报日前收盘价的百分比绝对值
- historical_avg_move_pct = 最近 8 次财报实际波动的均值
- 信号：implied > 1.5× historical_avg → sell_straddle；historical_avg > 1.5× implied → buy_straddle

### AC-3 降级策略

- 无 next_earnings_date → data_available=True，implied_move_pct=None，straddle_signal=unknown
- 无期权或 straddle 价格为 0 → implied_move_pct=None
- 无历史财报数据 → historical_avg_move_pct=None
- yfinance 完全失败 → data_available=False

### AC-4 测试要求

- 测试总数 ≥ 16
- 覆盖：_get_atm_straddle_cost 正常 + 边界（价格为 0、空链）
- 覆盖：_compute_historical_moves 正常 + 边界（不足 2 次财报）
- 覆盖：compute_earnings_calendar 正常（有期权 + 有历史）
- 覆盖：无 next_earnings_date → data_available=True，signal=unknown
- 覆盖：sell_straddle 信号（implied >> historical）
- 覆盖：buy_straddle 信号（historical >> implied）
- 覆盖：yfinance 异常 → data_available=False
- 覆盖：API GET /api/earnings-calendar，无 ticker 422，有 ticker 200
- 所有测试 mock 网络调用

### AC-5 API

- 路由：`GET /api/earnings-calendar?ticker=<TICKER>`
- 无 ticker → HTTP 422；有 ticker → 始终 200
- 通过 `include_with_api_alias(earnings_calendar_router)` 注册

### AC-6 前端

- `client.ts`：StraddleSignal / EarningsMove / EarningsCalendarData / fetchEarningsCalendar
- `EarningsCalendarPanel.tsx`：下次财报倒计时 + 隐含波动 vs 历史波动对比 + 信号徽章 + 历史记录表
- RiskReviewCenter.tsx 引入并渲染 `<EarningsCalendarPanel />`
- TypeScript tsc --noEmit 通过；Vite 构建通过

## 测试命令

```bash
cd apps/stock-assistant/backend && uv run pytest tests/test_earnings_calendar.py -v
```
