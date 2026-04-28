# Task phaseC.3.walk_forward: Walk-Forward CV + 滚动验证

**Phase**: C
**Status**: in-progress
**Created**: 2026-04-28
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 做什么

- 新建 `src/walk_forward.rs`：
  - `pub struct WalkForwardConfig { train_size, test_size, step_size, embargo_size }`
  - `pub struct WalkForwardWindow { train_start, train_end, test_start, test_end }`
  - `pub fn build_walk_forward_windows(total_rows: usize, config: &WalkForwardConfig) -> Vec<WalkForwardWindow>`：
    与 `quantpilot_quant.research.validation.build_walk_forward_windows` **逐行对齐**（cursor 起点、比较逻辑一致）
  - `pub fn run_walk_forward_ma_backtest(closes, fast_period, slow_period, initial_cash, config) -> Result<WalkForwardResult, String>`：
    对每个窗口：用训练集热身（以 initial_cash 进入），在测试集上跑 MA crossover，收集测试期 equity_curve；
    最终将各窗口测试期净值**复利链式拼接**（与 Python WalkForwardEngine._aggregate 对齐）
  - `pub struct WalkForwardResult { n_windows, equity_curve: Vec<f64>, window_splits: Vec<WalkForwardWindow> }`
- 在 `lib.rs` 添加 `pub mod walk_forward;` 和 `pub use walk_forward::*;`（或通过 `pub fn run_walk_forward_...` 暴露）
- 新建 `tools/golden-generator/src/quantpilot_golden/cases/walk_forward.py`：
  - `python_build_walk_forward_windows(total_rows, train_size, test_size, step_size, embargo_size) -> list[dict]`：
    与 Rust **逐行对齐**（不依赖 quantpilot_quant 内部实现，避免测试自引用）
  - `generate_walk_forward_splits_basic()`：在 100 根数据上跑若干窗口配置，输出各 case 的窗口索引
- 新建 `common/data-store/golden/expected/walk_forward_splits_basic.json`
- 新建 `apps/quant-assistant/backend/tests/walk_forward_test.rs`：
  - `walk_forward_splits_match_golden`：Rust build_walk_forward_windows 输出的每个窗口 (train_start, train_end, test_start, test_end) 与 golden **bit-identical**（plan §7 要求 0 误差）
  - `walk_forward_ma_backtest_runs`：run_walk_forward_ma_backtest 基本运行不报错，n_windows > 0，equity_curve 长度正确

### 不做什么

- 不实现参数网格搜索（那是 C.5.optimize 的事）；窗口内固定参数
- 不改变现有 run_ma_crossover_backtest 函数
- 不暴露 HTTP endpoint（留后续）
- 不实现 WalkForwardEngine 的 `_slice_to_test` 的完整版（本 task 只做训练窗口热身 + 测试窗口运行 + 链式拼接）

---

## 验收标准

- [ ] **AC-1**: `src/walk_forward.rs` 存在，含 `build_walk_forward_windows`, `WalkForwardConfig`, `WalkForwardWindow`
- [ ] **AC-2**: `lib.rs` 含 `pub mod walk_forward`
- [ ] **AC-3**: `common/data-store/golden/expected/walk_forward_splits_basic.json` 存在
- [ ] **AC-4**: `cargo test` 全过
- [ ] **AC-5**: `walk_forward_splits_match_golden` — Rust 窗口索引与 golden **bit-identical**（所有 start/end 字段完全一致）
- [ ] **AC-6**: `walk_forward_ma_backtest_runs` — run_walk_forward_ma_backtest 不报错，n_windows > 0
- [ ] **AC-7**: 已有测试不受影响（common 59、stock 165、quant-py 276）

---

## 测试集合

```bash
# AC-1
test -f apps/quant-assistant/backend/src/walk_forward.rs
grep -q "pub fn build_walk_forward_windows" apps/quant-assistant/backend/src/walk_forward.rs

# AC-2
grep -q "pub mod walk_forward" apps/quant-assistant/backend/src/lib.rs

# AC-3
test -f common/data-store/golden/expected/walk_forward_splits_basic.json

# AC-4 + AC-5 + AC-6
(cd apps/quant-assistant/backend && cargo test 2>&1 | grep "test result")
(cd apps/quant-assistant/backend && cargo test --test walk_forward_test 2>&1 | grep -q "test result: ok")

# AC-7
(cd common/python && uv run --group dev pytest tests/ -q | tail -2 | grep -q "59 passed")
(cd apps/stock-assistant/backend && uv run pytest tests/ -q | tail -2 | grep -q "165 passed")
(cd apps/quant-assistant-py/backend && uv run pytest tests/ -q | tail -2 | grep -q "276 passed")
```

---

## 文件影响范围（白名单）

```
- apps/quant-assistant/backend/src/walk_forward.rs (新建)
- apps/quant-assistant/backend/src/lib.rs
- apps/quant-assistant/backend/tests/walk_forward_test.rs (新建)
- common/data-store/golden/expected/walk_forward_splits_basic.json (新建)
- tools/golden-generator/src/quantpilot_golden/cases/walk_forward.py (新建)
- docs/tasks/phaseC/c3-walk-forward.md (本文件)
```

---

## 引用

- **设计来源**：plan §5 "C.3：walk-forward + 滚动验证"，plan §9 "phaseC.3.walk_forward"
- **算法参考**：`apps/quant-assistant-py/backend/src/quantpilot_quant/research/validation.py`
  + `apps/quant-assistant-py/backend/src/quantpilot_quant/backtest/walk_forward.py`
- **上游依赖**：phaseC.2.factor.sma（indicators 模块），phaseB.mvp.backtest（run_ma_crossover_backtest）
- **下游依赖**：phaseC.4.onnx，phaseC.5.optimize
