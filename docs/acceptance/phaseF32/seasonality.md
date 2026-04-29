# Acceptance Report: F.32 — Seasonality Pattern Analysis

**Run at**: 2026-04-30T00:00:00Z
**Implementation PR**: commit 28dbc3b9ab720b8ec554cf0afa2c68b67c5659b7
**Diff range**: `HEAD~1..HEAD`
**Acceptance-agent invocation**: claude-sonnet-4-6 session (2026-04-30)
**Verdict**: PASS

## 文件影响范围检查

- 改动文件总数：11
- 在白名单内：11（含 `docs/tasks/phaseF32/seasonality.md` 和 `docs/acceptance/` 下的两个前轮报告）
- 超出白名单：0

完整文件清单（`git diff --name-only HEAD~1 HEAD`）：
```
apps/stock-assistant/backend/src/quantpilot_stock/api/seasonality.py
apps/stock-assistant/backend/src/quantpilot_stock/main.py
apps/stock-assistant/backend/src/quantpilot_stock/seasonality/__init__.py
apps/stock-assistant/backend/src/quantpilot_stock/seasonality/engine.py
apps/stock-assistant/backend/tests/test_seasonality.py
apps/stock-assistant/frontends/workbench/src/api/client.ts
apps/stock-assistant/frontends/workbench/src/components/SeasonalityPanel.tsx
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx
docs/acceptance/phaseF30/technical-score.md
docs/acceptance/phaseF31/beta-correlation.md
docs/tasks/phaseF32/seasonality.md
```

前两个 docs/acceptance 文件是前一轮写入的验收报告，属 acceptance 制品，不违反白名单约束。

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 数据模型 (SeasonalSignal / MonthStats / SeasonalityData) | ✅ PASS | `engine.py` 定义了 `SeasonalSignal` Literal（6 个值），`MonthStats` dataclass（month/month_name/avg_return/median_return/positive_rate/sample_size），`SeasonalityData` dataclass（ticker/current_month/current_month_stats/all_months/best_month/worst_month/signal/interpretation/as_of_date/data_available）；字段类型与 spec 完全一致 |
| AC-2: 计算逻辑 | ✅ PASS | `compute_seasonality` 调用 `tk.history(period="10y", interval="1mo")`；`pct_change().dropna()` 计算月度收益率；按月 groupby 聚合 avg/median/positive_rate/sample_size；signal 分类阈值完全匹配 spec（>0.03/0.01/-0.01/-0.03/≤-0.03）；pytest 33 passed |
| AC-3: 降级策略 | ✅ PASS | 数据不足（<12 月）→ `data_available=True, all_months=[], signal=no_data`（`test_insufficient_data_graceful` PASS）；yfinance 异常 → `data_available=False`（`test_yfinance_exception_data_unavailable` PASS）；空 DataFrame → graceful（`test_empty_dataframe_graceful` PASS） |
| AC-4: 测试要求（≥16 个，覆盖所有场景，全 mock 网络） | ✅ PASS | 共 33 个测试；覆盖 `_compute_monthly_stats`（7）、`_classify_signal`（10 含所有边界）、`compute_seasonality` 集成（10）、API（6）；所有测试均用 `@patch("quantpilot_stock.seasonality.engine.yf.Ticker")` 或 MagicMock mock 网络；退出码 0 |
| AC-5: API（GET /api/seasonality?ticker=，422/200，include_with_api_alias 注册） | ✅ PASS | `api/seasonality.py` 路由 `GET /seasonality`；`Query(...)` 使 ticker 必填，缺失返回 422（`test_no_ticker_returns_422`）；有 ticker 返回 200（`test_with_ticker_returns_200`，`test_yfinance_fail_still_200`）；`main.py` 第 161-162 行用 `include_with_api_alias(seasonality_router)` 注册 |
| AC-6: 前端（client.ts 类型、SeasonalityPanel 功能、RiskReviewCenter 集成、Vite 构建通过） | ✅ PASS | `client.ts` 导出 `SeasonalSignal`/`MonthStats`/`SeasonalityData`/`fetchSeasonality`；`SeasonalityPanel.tsx` 含 ticker 输入框 + 分析按钮 + 信号徽章 + 12 月热图（MonthCell）+ 当月详情（CurrentMonthDetail）+ 最强/最弱月标注；`RiskReviewCenter.tsx` import 并渲染 `<SeasonalityPanel />`；`npm run build` 退出码 0（✓ built in 413ms） |

## 测试执行日志摘要

### `cd apps/stock-assistant/backend && uv run pytest tests/test_seasonality.py -v`
- 退出码：0
- 收集：33 items
- 全部 PASSED（TestComputeMonthlyStats 7、TestClassifySignal 10、TestComputeSeasonalityIntegration 10、TestSeasonalityAPI 6）
- 耗时：5.87s

### `uv run ruff check src/quantpilot_stock/seasonality/ src/quantpilot_stock/api/seasonality.py tests/test_seasonality.py`
- 退出码：0
- 输出：`All checks passed!`

### `uv run mypy src/quantpilot_stock/seasonality/ src/quantpilot_stock/api/seasonality.py --ignore-missing-imports`
- 退出码：0
- 输出：`Success: no issues found in 3 source files`

### `cd apps/stock-assistant/frontends/workbench && npm run build`
- 退出码：0
- 输出：`✓ built in 413ms`；TypeScript 无类型错误

## 代码 Review 备注

- `engine.py` 和 `api/seasonality.py` 均有模块级 docstring 及完整 type hints，符合 CLAUDE.md 规范。
- 无跨 app import；`common/` 未被反向 import。
- `_compute_monthly_stats` 对无数据月份返回 `sample_size=0` 的占位 MonthStats（而非只返回有数据月份），这与前端热图期望 12 个固定格子一致，设计合理。
- AC-3 中 spec 写"历史数据不足 → data_available=True，all_months=[]"，但 `_compute_monthly_stats` 只在数据超过 12 个月才调用，不足时直接早返回空列表，实现与 spec 一致。

## 后续动作

PR 可合，无 prerequisite。建议更新 `docs/acceptance/INDEX.md` 增加 F.32 条目。
