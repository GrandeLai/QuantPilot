# Task F.28 — 股息分析面板 (Dividend Analysis)

## 背景

对于收入投资者和短线股息捕获策略，股息数据是核心决策因素：
- **股息捕获策略**：在 Ex-Date 前 T-2 买入，持有至股息获得后卖出，历史每次 0.5-3% alpha
- **股息增长投资**：连续增长年限（Dividend Aristocrat ≥ 25 年；Dividend King ≥ 50 年）
- **派息安全性**：Payout Ratio < 75% 为安全；> 100% 为危险信号（靠借债分红）
- **收益率对比**：股息率 vs 10 年国债收益率，判断股息股的相对吸引力

数据来源：yfinance（免费）

## 范围（文件白名单）

```
apps/stock-assistant/backend/src/quantpilot_stock/dividend_analysis/__init__.py
apps/stock-assistant/backend/src/quantpilot_stock/dividend_analysis/engine.py
apps/stock-assistant/backend/src/quantpilot_stock/api/dividend_analysis.py
apps/stock-assistant/backend/src/quantpilot_stock/main.py
apps/stock-assistant/backend/tests/test_dividend_analysis.py
apps/stock-assistant/frontends/workbench/src/api/client.ts
apps/stock-assistant/frontends/workbench/src/components/DividendAnalysisPanel.tsx
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx
docs/tasks/phaseF28/dividend-analysis.md
```

## 验收标准（AC）

### AC-1 数据模型

- `DividendSafety` = Literal["safe","watch","danger","no_dividend"]
- `DividendCaptureSignal` = Literal["capture_opportunity","not_applicable","unknown"]
- `DividendAnalysisData` dataclass：ticker, dividend_yield, annual_dividend, payout_ratio,
  ex_dividend_date, days_to_ex_date, dividend_frequency, five_yr_growth_rate,
  consecutive_growth_years, safety, capture_signal, interpretation, as_of_date, data_available

### AC-2 计算逻辑

- five_yr_growth_rate = CAGR 5 年股息增长（历史 `tk.dividends`）
  - 最早与最新年度股息之比，取 5 年 CAGR
- consecutive_growth_years = 连续增长年数（逐年对比年度总股息）
- Payout Safety：
  - payout_ratio < 0.75 → safe
  - 0.75-1.0 → watch
  - ≥ 1.0 → danger
  - 无 dividend_yield → no_dividend
- capture_signal：days_to_ex_date 0-5 → capture_opportunity；其余 → not_applicable

### AC-3 降级策略

- 无股息 → data_available=True，safety=no_dividend，capture_signal=not_applicable
- yfinance 失败 → data_available=False

### AC-4 测试要求

- 测试总数 ≥ 16
- 覆盖：_compute_dividend_growth 正常 + 不足 2 年数据
- 覆盖：_compute_consecutive_growth 正常 + 中断增长
- 覆盖：_classify_safety 所有档位 + no_dividend
- 覆盖：capture_signal 逻辑（DTE ≤ 5 vs > 5）
- 覆盖：compute_dividend_analysis 正常（有股息）
- 覆盖：无股息股票 → safety=no_dividend
- 覆盖：yfinance 异常 → data_available=False
- 覆盖：API GET /api/dividend-analysis?ticker=，无 ticker 422，有 ticker 200
- 所有测试 mock 网络调用

### AC-5 API

- 路由：`GET /api/dividend-analysis?ticker=<TICKER>`
- 无 ticker → HTTP 422；有 ticker → 始终 200
- 通过 `include_with_api_alias(dividend_analysis_router)` 注册

### AC-6 前端

- `client.ts`：DividendSafety / DividendCaptureSignal / DividendAnalysisData / fetchDividendAnalysis
- `DividendAnalysisPanel.tsx`：安全评级 + ex-date 倒计时 + 收益率 + 增长记录 + 股息捕获信号
- RiskReviewCenter.tsx 引入并渲染 `<DividendAnalysisPanel />`
- TypeScript tsc --noEmit 通过；Vite 构建通过

## 测试命令

```bash
cd apps/stock-assistant/backend && uv run pytest tests/test_dividend_analysis.py -v
```
