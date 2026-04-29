# Task F.32 — 季节性模式分析 (Seasonality Pattern Analysis)

## 背景

股票市场存在被充分记录的季节性 Alpha：
- **一月效应**：一月份中小盘股历史超额收益（税损卖出后反弹）
- **卖五月（Sell in May）**：5-10 月历史收益率低于 11-4 月
- **圣诞行情**：12-1 月年底效应
- **月份动量**：特定行业在特定月份历史表现规律

基于历史 5-10 年月度数据，量化每个月的历史平均/中位收益率，为择时决策提供参考。

数据来源：yfinance（免费，最多 10 年月度数据）

## 范围（文件白名单）

```
apps/stock-assistant/backend/src/quantpilot_stock/seasonality/__init__.py
apps/stock-assistant/backend/src/quantpilot_stock/seasonality/engine.py
apps/stock-assistant/backend/src/quantpilot_stock/api/seasonality.py
apps/stock-assistant/backend/src/quantpilot_stock/main.py
apps/stock-assistant/backend/tests/test_seasonality.py
apps/stock-assistant/frontends/workbench/src/api/client.ts
apps/stock-assistant/frontends/workbench/src/components/SeasonalityPanel.tsx
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx
docs/tasks/phaseF32/seasonality.md
```

## 验收标准（AC）

### AC-1 数据模型

- `SeasonalSignal` = Literal["strong_season","positive_season","neutral","negative_season","strong_negative","no_data"]
- `MonthStats` dataclass：month（1-12），month_name，avg_return，median_return，
  positive_rate（正收益月份比例），sample_size
- `SeasonalityData` dataclass：ticker, current_month, current_month_stats,
  all_months: list[MonthStats], best_month（avg最高月份编号），worst_month（avg最低月份编号），
  signal，interpretation，as_of_date，data_available

### AC-2 计算逻辑

- 获取最近 max_years=10 年的月度收盘价（tk.history(period="10y", interval="1mo")）
- 月度收益率 = pct_change()，去掉 NaN
- 按月聚合（groupby month）：avg_return, median_return, positive_rate, sample_size
- current_month = date.today().month
- Signal（基于当前月份的历史平均收益）：
  - avg_return > 3% → strong_season
  - avg_return > 1% → positive_season
  - avg_return > -1% → neutral
  - avg_return > -3% → negative_season
  - avg_return ≤ -3% → strong_negative
  - 无数据 → no_data

### AC-3 降级策略

- 历史数据不足（< 12 个月）→ data_available=True，all_months=[]，signal=no_data
- yfinance 失败 → data_available=False

### AC-4 测试要求

- 测试总数 ≥ 16
- 覆盖：_compute_monthly_stats 正常 + 空数据
- 覆盖：_classify_signal 所有档位
- 覆盖：compute_seasonality 正常 + 不足数据 + yfinance 失败
- 覆盖：API GET /api/seasonality?ticker=，无 ticker 422，有 ticker 200
- 所有测试 mock 网络调用

### AC-5 API

- 路由：`GET /api/seasonality?ticker=<TICKER>`
- 无 ticker → HTTP 422；有 ticker → 始终 200
- 通过 `include_with_api_alias(seasonality_router)` 注册

### AC-6 前端

- `client.ts`：SeasonalSignal / MonthStats / SeasonalityData / fetchSeasonality
- `SeasonalityPanel.tsx`：
  - ticker 输入框 + 分析按钮
  - 当前月份信号徽章
  - 12 个月月度热图（颜色深浅表示平均收益率高低）
  - 当月详情（avg/median/正收益率/样本量）
  - 最强/最弱月份标注
- RiskReviewCenter.tsx 引入并渲染 `<SeasonalityPanel />`
- TypeScript tsc --noEmit 通过；Vite 构建通过

## 测试命令

```bash
cd apps/stock-assistant/backend && uv run pytest tests/test_seasonality.py -v
```
