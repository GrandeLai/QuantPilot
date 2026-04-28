# Task phaseC.6.reports: 回测报告 + 绩效指标全集

**Phase**: C
**Status**: in-progress
**Created**: 2026-04-28
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 做什么

- 新建 `src/reports.rs`：
  - `pub struct BacktestReport`：
    - 收益类：`total_return, annual_return` (CAGR)
    - 风险类：`max_drawdown, max_drawdown_start, max_drawdown_end, volatility`
    - 风险调整收益：`sharpe_ratio, sortino_ratio, calmar_ratio`
    - 统计类：`total_bars, trading_days`
  - `pub fn calculate_report(equity_curve, initial_cash, risk_free_rate, periods_per_year) -> BacktestReport`：
    逐项计算所有指标（与 Python `backtest/metrics.py::calculate_metrics` 对齐）
  - `pub fn format_report_text(report: &BacktestReport) -> String`：简单文本摘要（无外部模板库依赖）
- 在 `lib.rs` 添加 `pub mod reports;`
- 新建 `tools/golden-generator/src/quantpilot_golden/cases/reports.py`：
  - `python_calculate_report(equity_curve, initial_cash, risk_free_rate, periods_per_year) -> dict`：
    与 Rust 逐行对齐的独立 Python 实现（不依赖 quantpilot_quant）
  - `generate_reports_basic()`：用 25 根固定 K 线的 MA crossover equity curve 计算全套指标
- 新建 `common/data-store/golden/expected/reports_basic.json`
- 新建 `apps/quant-assistant/backend/tests/reports_test.rs`：
  - `report_metrics_match_golden`：各指标与 golden 在 1e-9 容差内
  - `sortino_ratio_positive_for_uptrend`：上行趋势时 sortino > 0
  - `calmar_ratio_equals_annual_return_div_max_drawdown`：calmar = annual_return / max_drawdown

### 不做什么

- 不实现 Jinja2 模板 Markdown 报告（模板渲染留后续）
- 不实现 Feishu 推送（feishu_doc.py 对应功能）
- 不删除 quant-py reports/（step4 整体清理）
- 不计算 win_rate/profit_factor（需要 TradeRecord，MVP 先做纯 equity_curve 指标）

---

## 验收标准

- [ ] **AC-1**: `src/reports.rs` 存在，含 `calculate_report` 和 `format_report_text`
- [ ] **AC-2**: `lib.rs` 含 `pub mod reports`
- [ ] **AC-3**: `common/data-store/golden/expected/reports_basic.json` 存在
- [ ] **AC-4**: `cargo test` 全过
- [ ] **AC-5**: `report_metrics_match_golden` 各指标在 1e-9 内
- [ ] **AC-6**: `sortino_ratio_positive_for_uptrend` 通过
- [ ] **AC-7**: 已有测试不受影响（common 59、stock 165、quant-py 276）

---

## 测试集合

```bash
# AC-1
test -f apps/quant-assistant/backend/src/reports.rs
grep -q "pub fn calculate_report" apps/quant-assistant/backend/src/reports.rs

# AC-2
grep -q "pub mod reports" apps/quant-assistant/backend/src/lib.rs

# AC-3
test -f common/data-store/golden/expected/reports_basic.json

# AC-4 + AC-5 + AC-6
(cd apps/quant-assistant/backend && cargo test 2>&1 | grep "test result")
(cd apps/quant-assistant/backend && cargo test --test reports_test 2>&1 | grep -q "test result: ok")

# AC-7
(cd common/python && uv run --group dev pytest tests/ -q | tail -2 | grep -q "59 passed")
(cd apps/stock-assistant/backend && uv run pytest tests/ -q | tail -2 | grep -q "165 passed")
(cd apps/quant-assistant-py/backend && uv run pytest tests/ -q | tail -2 | grep -q "276 passed")
```

---

## 文件影响范围（白名单）

```
- apps/quant-assistant/backend/src/reports.rs (新建)
- apps/quant-assistant/backend/src/lib.rs
- apps/quant-assistant/backend/tests/reports_test.rs (新建)
- common/data-store/golden/expected/reports_basic.json (新建)
- tools/golden-generator/src/quantpilot_golden/cases/reports.py (新建)
- docs/tasks/phaseC/c6-reports.md (本文件)
```

---

## 引用

- **算法参考**：`apps/quant-assistant-py/.../backtest/metrics.py::calculate_metrics`
- **上游依赖**：phaseB.mvp.backtest（run_ma_crossover_backtest, sharpe_ratio, max_drawdown），phaseC.2.factor.sma
