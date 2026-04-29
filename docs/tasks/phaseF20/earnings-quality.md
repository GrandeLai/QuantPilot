# Task F.20 — 盈利质量三件套 (Earnings Quality Scoring)

## 背景

为 RiskReviewCenter 新增盈利质量综合评分面板，基于三种学术验证方法：
- **Piotroski F-Score**（0-9）：盈利/杠杆/运营效率综合改善情况（Piotroski 2000）
- **Beneish M-Score**：8 因子盈利操纵检测模型，阈值 -2.22（Beneish 1999）
- **Sloan 应计比率**：(Net Income - CFO) / Avg Total Assets，超 ±10% = 低质量（Sloan 1996）

数据来源：yfinance 年度财报（financials / balance_sheet / cashflow），无需付费数据。

## 范围（文件白名单）

```
apps/stock-assistant/backend/src/quantpilot_stock/earnings_quality/__init__.py
apps/stock-assistant/backend/src/quantpilot_stock/earnings_quality/engine.py
apps/stock-assistant/backend/src/quantpilot_stock/api/earnings_quality.py
apps/stock-assistant/backend/src/quantpilot_stock/main.py
apps/stock-assistant/backend/tests/test_earnings_quality.py
apps/stock-assistant/frontends/workbench/src/api/client.ts
apps/stock-assistant/frontends/workbench/src/components/EarningsQualityPanel.tsx
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx
docs/tasks/phaseF20/earnings-quality.md
```

## 验收标准（AC）

### AC-1 数据模型

- `EarningsQualityGrade` = Literal["high_quality","average_quality","low_quality","manipulator_risk"]
- `FScoreGrade` = Literal["very_strong","strong","average","weak"]
- `AccrualQuality` = Literal["high","medium","low"]
- `EarningsQualityData` dataclass 包含字段：
  `ticker, f_score, f_score_grade, f_score_components, m_score, manipulation_risk,
   accrual_ratio, accrual_quality, quality_grade, interpretation, as_of_date, data_available`

### AC-2 Piotroski F-Score 计算

9 个子指标（各 1 分）：
- Profitability: ROA>0, CFO>0, ΔROA>0, CFO/Assets > NI/Assets（accrual OK）
- Leverage: ΔLeverage↓, ΔCurrentRatio↑, No new shares
- Efficiency: ΔGross Margin↑, ΔAsset Turnover↑

等级：8-9=very_strong, 6-7=strong, 3-5=average, 0-2=weak

### AC-3 Beneish M-Score 计算

8 指数（DSRI/GMI/AQI/SGI/DEPI/SGAI/LVGI/TATA）加权求和，截距 -4.84
- M > -2.22 → manipulation_risk = True

### AC-4 Sloan 应计比率

- accrual_ratio = (NetIncome - CFO) / ((TotalAssets_t + TotalAssets_t-1) / 2)
- |ratio| ≤ 5% → high; |ratio| ≤ 10% → medium; else → low

### AC-5 测试要求

- 测试总数 ≥ 16（实际 44）
- 覆盖：_safe_get（存在键/缺失键/多键/nan）
- 覆盖：F-Score 改善/恶化场景 + 空 DataFrame
- 覆盖：M-Score float 返回 + 空 DataFrame
- 覆盖：应计比率 high/medium/low + 缺失数据
- 覆盖：_overall_grade 所有分支
- 覆盖：compute_earnings_quality happy path + 异常 → data_available=False
- 覆盖：API GET /api/earnings-quality?ticker=，无 ticker 422，有 ticker 200
- 所有测试 mock yfinance，不发真实网络请求

### AC-6 API

- 路由：`GET /api/earnings-quality?ticker=<TICKER>`
- 无 ticker → HTTP 422
- 有 ticker → 始终 HTTP 200，返回 EarningsQualityData JSON
- 通过 `include_with_api_alias(earnings_quality_router)` 注册

### AC-7 前端

- `client.ts` 包含 `EarningsQualityGrade`/`FScoreGrade`/`AccrualQuality` 类型、`EarningsQualityData` 接口、`fetchEarningsQuality` 函数
- `EarningsQualityPanel.tsx` 实现：
  - 综合评级 badge
  - Piotroski F-Score 条形图 + 9 个子指标 Pass/Fail 列表
  - Beneish M-Score 指示器（含 -2.22 阈值标注）
  - Sloan 应计比率 + 质量等级
  - 降级提示 banner
- `RiskReviewCenter.tsx` 引入并渲染 `<EarningsQualityPanel />`
- TypeScript 类型检查通过（`tsc --noEmit`）
- Vite 生产构建通过

## 测试命令

```bash
cd apps/stock-assistant/backend && uv run pytest tests/test_earnings_quality.py -v
```

## 静态检查命令

```bash
cd apps/stock-assistant/backend && uv run ruff check src/quantpilot_stock/earnings_quality/ src/quantpilot_stock/api/earnings_quality.py tests/test_earnings_quality.py
cd apps/stock-assistant/backend && uv run mypy src/quantpilot_stock/earnings_quality/ src/quantpilot_stock/api/earnings_quality.py
```
