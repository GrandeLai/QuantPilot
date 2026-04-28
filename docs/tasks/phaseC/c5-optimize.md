# Task phaseC.5.optimize: 策略参数优化（网格搜索）

**Phase**: C
**Status**: in-progress
**Created**: 2026-04-28
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 做什么

- 新建 `src/optimizer.rs`：
  - `pub struct GridSearchConfig { fast_periods: Vec<usize>, slow_periods: Vec<usize> }`
  - `pub struct OptimizeResult { fast_period, slow_period, sharpe_ratio, total_return, max_drawdown }`
  - `pub fn grid_search_ma_crossover(closes, initial_cash, config, risk_free_rate, periods_per_year) -> Vec<OptimizeResult>`：
    穷举所有 (fast_period, slow_period) 组合（fast < slow 才有意义），对每组跑 `run_ma_crossover_backtest`，
    计算 Sharpe + max_drawdown，返回按 Sharpe 降序排列的结果列表
- 在 `lib.rs` 添加 `pub mod optimizer;`
- 新建 `tools/golden-generator/src/quantpilot_golden/cases/optimizer.py`：
  - `python_grid_search_ma_crossover(closes, initial_cash, fast_periods, slow_periods, risk_free, periods_per_year)`：
    与 Rust 逐行对齐（调 python_ma_crossover_backtest, python_sharpe_ratio, python_max_drawdown）
  - `generate_optimizer_grid_basic()`：用 25 根固定 K 线跑 3×3 组合网格，生成 golden case
- 新建 `common/data-store/golden/expected/optimizer_grid_basic.json`
- 新建 `apps/quant-assistant/backend/tests/optimizer_test.rs`：
  - `grid_search_results_match_golden`：Rust 每组合的 (sharpe, total_return, max_drawdown) 与 golden 等价（容差 1e-9）
  - `grid_search_returns_sorted_by_sharpe`：结果按 Sharpe 降序
  - `grid_search_skips_invalid_combos`：fast >= slow 的组合不出现在结果中

### 不做什么

- 不实现贝叶斯优化（Optuna，留 C.5.b 或 step4 后）
- 不实现 portfolio weights 优化（与 clarabel-rs 的集成留更后续）
- 不在 HTTP 端点暴露（留后续）
- 不删除 quant-py 的 OptimizationEngine（step4 整体清理）

---

## 验收标准

- [ ] **AC-1**: `src/optimizer.rs` 存在，含 `grid_search_ma_crossover`
- [ ] **AC-2**: `lib.rs` 含 `pub mod optimizer`
- [ ] **AC-3**: `common/data-store/golden/expected/optimizer_grid_basic.json` 存在
- [ ] **AC-4**: `cargo test` 全过
- [ ] **AC-5**: `grid_search_results_match_golden` — 各组合 metrics 在 1e-9 容差内
- [ ] **AC-6**: `grid_search_returns_sorted_by_sharpe` 通过
- [ ] **AC-7**: 已有测试不受影响（common 59、stock 165、quant-py 276）

---

## 测试集合

```bash
# AC-1
test -f apps/quant-assistant/backend/src/optimizer.rs
grep -q "pub fn grid_search_ma_crossover" apps/quant-assistant/backend/src/optimizer.rs

# AC-2
grep -q "pub mod optimizer" apps/quant-assistant/backend/src/lib.rs

# AC-3
test -f common/data-store/golden/expected/optimizer_grid_basic.json

# AC-4 + AC-5 + AC-6
(cd apps/quant-assistant/backend && cargo test 2>&1 | grep "test result")
(cd apps/quant-assistant/backend && cargo test --test optimizer_test 2>&1 | grep -q "test result: ok")

# AC-7
(cd common/python && uv run --group dev pytest tests/ -q | tail -2 | grep -q "59 passed")
(cd apps/stock-assistant/backend && uv run pytest tests/ -q | tail -2 | grep -q "165 passed")
(cd apps/quant-assistant-py/backend && uv run pytest tests/ -q | tail -2 | grep -q "276 passed")
```

---

## 文件影响范围（白名单）

```
- apps/quant-assistant/backend/src/optimizer.rs (新建)
- apps/quant-assistant/backend/src/lib.rs
- apps/quant-assistant/backend/tests/optimizer_test.rs (新建)
- common/data-store/golden/expected/optimizer_grid_basic.json (新建)
- tools/golden-generator/src/quantpilot_golden/cases/optimizer.py (新建)
- docs/tasks/phaseC/c5-optimize.md (本文件)
```

---

## 引用

- **设计来源**：plan §5 "C.5：优化（osqp/clarabel-rs）"，plan §9 "phaseC.5.optimize"
- **算法参考**：`apps/quant-assistant-py/.../optimize/engine.py::OptimizationEngine.grid_search`
- **上游依赖**：phaseB.mvp.backtest（run_ma_crossover_backtest, sharpe_ratio, max_drawdown）
