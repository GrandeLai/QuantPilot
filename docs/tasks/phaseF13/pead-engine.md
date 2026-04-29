# Task F.13: PEAD — Post-Earnings Announcement Drift

## 背景与目的

PEAD (Post-Earnings Announcement Drift, Bernard & Thomas 1989) 是最持久的市场异常之一：
- **盈利超预期 → 价格在未来 60-90 天持续上涨**（动量）
- **盈利低于预期 → 价格持续下跌**（反向动量）
- 学术证明：大幅超预期股票 90 日超额 +6-8%；大幅低于预期 −6-8%

本任务实现 PEAD 信号引擎（`pead/engine.py`）、API 端点（`api/pead.py`）和前端面板（`PEADPanel.tsx`）。

## 验收标准（AC）

### AC-1 引擎（pead/engine.py）
- [ ] `EarningsSurpriseGrade = Literal["large_beat","beat","inline","miss","large_miss"]`
- [ ] `EarningsEvent` dataclass：earnings_date, actual_eps, estimated_eps, surprise_pct, grade
- [ ] `PEADSignal` dataclass：ticker, last_earnings, expected_drift_30d/60d/90d, next_earnings_date, interpretation, as_of_date
- [ ] `_surprise_grade(pct)` → grade 阈值：>+10% large_beat, +2~10% beat, -2~2% inline, -10~-2% miss, <-10% large_miss
- [ ] `PEAD_DRIFT` 字典：每档 grade 给出 30d/60d/90d 预期漂移（基于学术研究）
- [ ] `compute_pead_signal(ticker)` → `PEADSignal | None`：数据不足返回 None，不抛异常
- [ ] 使用 yfinance `ticker.earnings_dates`（取最近已报告的那一条）+ `ticker.calendar` 获取下一次财报日

### AC-2 API（api/pead.py）
- [ ] `GET /api/pead?ticker=AAPL` → 200 + PEADSignalResponse
- [ ] 无数据 → 404
- [ ] 缺 ticker → 422
- [ ] 路由通过 `include_with_api_alias` 注册

### AC-3 前端（PEADPanel.tsx + client.ts）
- [ ] `PEADSignalData`、`EarningsEventData` 类型加入 `client.ts`
- [ ] `fetchPEADSignal(ticker)` 函数加入 `client.ts`
- [ ] `PEADPanel.tsx` 展示：surprise % + grade badge + 30/60/90d 预期漂移条 + 下次财报日
- [ ] `PEADPanel` 加入 `RiskReviewCenter.tsx`
- [ ] TypeScript 构建无报错

### AC-4 测试（≥ 18 个）
- [ ] `_surprise_grade` 全档边界
- [ ] `compute_pead_signal` happy path：grade、drift 正确
- [ ] 空 earnings_dates → None
- [ ] 异常（yf 抛出）→ None
- [ ] API 200/404/422

## 文件白名单

- `apps/stock-assistant/backend/src/quantpilot_stock/pead/__init__.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/pead/engine.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/api/pead.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`
- `apps/stock-assistant/backend/tests/test_pead.py`
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`
- `apps/stock-assistant/frontends/workbench/src/components/PEADPanel.tsx`
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
- `docs/tasks/phaseF13/pead-engine.md`
- `docs/acceptance/phaseF13/pead-engine.md`

## PEAD 漂移参考值（来源：Bernard & Thomas 1989, Livnat & Mendenhall 2006）

| 等级 | 30d | 60d | 90d |
|---|---|---|---|
| large_beat | +3.5% | +5.2% | +6.8% |
| beat | +1.8% | +2.8% | +3.5% |
| inline | 0.0% | 0.0% | 0.0% |
| miss | −1.8% | −2.8% | −3.5% |
| large_miss | −3.5% | −5.2% | −6.8% |

> 注：以上为学术研究均值，实际会因市值/流动性/行业而异。展示时需加"仅供参考"免责声明。
