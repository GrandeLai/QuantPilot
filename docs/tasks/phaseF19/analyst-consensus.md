# Task F.19 — 分析师共识 & 目标价面板 (Analyst Consensus & Price Target)

## 背景

为 RiskReviewCenter 新增华尔街分析师综合评级与 12 个月目标价面板，使用 yfinance 免费数据。
评级来源 `recommendationMean`（1=强烈买入，5=强烈卖出），目标价三档（高/中/低）及隐含涨跌幅。

## 范围（文件白名单）

```
apps/stock-assistant/backend/src/quantpilot_stock/analyst_consensus/__init__.py
apps/stock-assistant/backend/src/quantpilot_stock/analyst_consensus/engine.py
apps/stock-assistant/backend/src/quantpilot_stock/api/analyst_consensus.py
apps/stock-assistant/backend/src/quantpilot_stock/main.py
apps/stock-assistant/backend/tests/test_analyst_consensus.py
apps/stock-assistant/frontends/workbench/src/api/client.ts
apps/stock-assistant/frontends/workbench/src/components/AnalystConsensusPanel.tsx
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx
docs/tasks/phaseF19/analyst-consensus.md
```

## 验收标准（AC）

### AC-1 数据模型

- `AnalystGrade` = Literal["strong_buy","buy","hold","sell","strong_sell","no_coverage"]
- `AnalystConsensusData` dataclass 包含字段：
  `ticker, recommendation_mean, recommendation_key, num_analysts,
   target_mean_price, target_high_price, target_low_price, current_price,
   upside_pct, grade, interpretation, as_of_date, data_available`

### AC-2 评分区间

| recommendationMean | grade |
|---|---|
| ≤ 1.5 | strong_buy |
| ≤ 2.5 | buy |
| ≤ 3.5 | hold |
| ≤ 4.5 | sell |
| > 4.5 | strong_sell |
| None | no_coverage |

### AC-3 计算逻辑

- `upside_pct = (target_mean_price / current_price - 1) * 100`（两者均不为 None 时）
- `current_price` 依次取 `info["regularMarketPrice"]` 或 `info["currentPrice"]`
- `num_analysts` 取 `info["numberOfAnalystOpinions"]`，默认 0

### AC-4 测试要求

- 测试总数 ≥ 16（实际 25）
- 覆盖：grade 边界（≤1.5, 1.6, 2.5, 2.6, 3.5, 3.6, 4.5, 4.6, 5.0, None）
- 覆盖：happy path strong_buy/hold/strong_sell
- 覆盖：upside_pct 计算精度（误差 < 0.1%）
- 覆盖：ticker 大写化
- 覆盖：yfinance 抛出异常时 data_available=False
- 覆盖：API GET /api/analyst-consensus?ticker=，无 ticker 422，有 ticker 200
- 覆盖：degraded 时 as_of_date = date.today()
- 所有测试 mock yfinance，不发真实网络请求

### AC-5 API

- 路由：`GET /api/analyst-consensus?ticker=<TICKER>`
- 无 ticker 参数 → HTTP 422
- 有 ticker → 始终 HTTP 200，返回 AnalystConsensusData JSON
- 通过 `include_with_api_alias(analyst_consensus_router)` 注册

### AC-6 前端

- `client.ts` 包含 `AnalystGrade` 类型、`AnalystConsensusData` 接口、`fetchAnalystConsensus` 函数
- `AnalystConsensusPanel.tsx` 实现：
  - Grade badge（颜色编码）
  - RecommendationMeter 评分条（1-5 倒置显示）
  - 目标价网格（当前价 / 目标低 / 目标均值 / 目标高 / 隐含涨跌）
  - 降级提示 banner
- `RiskReviewCenter.tsx` 引入并渲染 `<AnalystConsensusPanel />`
- TypeScript 类型检查通过（`tsc --noEmit`）
- Vite 生产构建通过

## 测试命令

```bash
cd apps/stock-assistant/backend && uv run pytest tests/test_analyst_consensus.py -v
```

## 静态检查命令

```bash
cd apps/stock-assistant/backend && uv run ruff check src/quantpilot_stock/analyst_consensus/ src/quantpilot_stock/api/analyst_consensus.py tests/test_analyst_consensus.py
cd apps/stock-assistant/backend && uv run mypy src/quantpilot_stock/analyst_consensus/ src/quantpilot_stock/api/analyst_consensus.py
```
