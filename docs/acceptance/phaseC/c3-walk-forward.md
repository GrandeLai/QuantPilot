# Acceptance Report: phaseC.3.walk_forward

**Run at**: 2026-04-28T04:30:00Z
**Implementation PR/commit**: `1829c0f` — feat(quant-rust): Walk-Forward CV + window splitter + golden test (Phase C.3)
**Diff range**: commit `1829c0f` (single commit, 6 files, +857 lines)
**Acceptance-agent invocation**: Manual invocation by user
**Verdict**: ✅ **PASS** — Walk-Forward 窗口切割 bit-identical + MA 回测链式拼接 + golden 等价验证全部通过

---

## 文件影响范围检查

PR 改动 6 文件，全部在白名单内：

- `apps/quant-assistant/backend/src/walk_forward.rs` ✅（新建）
- `apps/quant-assistant/backend/src/lib.rs` ✅（添加 pub mod walk_forward）
- `apps/quant-assistant/backend/tests/walk_forward_test.rs` ✅（新建）
- `common/data-store/golden/expected/walk_forward_splits_basic.json` ✅（新建）
- `docs/tasks/phaseC/c3-walk-forward.md` ✅（任务规格）
- `tools/golden-generator/src/quantpilot_golden/cases/walk_forward.py` ✅（新建）

无超出白名单。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: `src/walk_forward.rs` 存在，含 `build_walk_forward_windows`, `WalkForwardConfig`, `WalkForwardWindow` | ✅ PASS | 文件存在；`grep pub fn build_walk_forward_windows` 命中；`WalkForwardConfig` 和 `WalkForwardWindow` 均为 `pub struct` |
| AC-2: `lib.rs` 含 `pub mod walk_forward` | ✅ PASS | `grep pub mod walk_forward lib.rs` 命中 |
| AC-3: `common/data-store/golden/expected/walk_forward_splits_basic.json` 存在 | ✅ PASS | 文件存在，含 4 个配置案例（basic_no_embargo、with_embargo、realistic_100bars、insufficient_data） |
| AC-4: `cargo test` 全过 | ✅ PASS | 34 tests total, 0 failed（17 lib + 2 bin + 1 golden + 4 indicators + 2 rhai + 4 walk_forward + 4 doc）|
| AC-5: `walk_forward_splits_match_golden` — Rust 窗口索引与 golden bit-identical | ✅ PASS | `walk_forward_splits_match_golden` ok；整数索引 bit-identical（tolerance abs=0） |
| AC-6: `walk_forward_ma_backtest_runs` — run_walk_forward_ma_backtest 不报错，n_windows > 0 | ✅ PASS | `walk_forward_ma_backtest_runs` ok；n_windows > 0，equity_curve 非空 |
| AC-7: 已有测试不受影响（common 59、stock 165、quant-py 276） | ✅ PASS | common 59 passed / stock 165 passed / quant-py 276 passed（3 warnings，无 errors） |

---

## 测试执行日志摘要

```
=== AC-1~AC-3: 文件 & grep 检查 ===
walk_forward.rs: OK
pub fn build_walk_forward_windows: OK
pub mod walk_forward: OK
walk_forward_splits_basic.json: OK

=== cargo test --test walk_forward_test (4 tests) ===
test walk_forward_backtest_too_few_rows_is_err  ok
test walk_forward_equity_starts_at_initial_cash ok
test walk_forward_ma_backtest_runs              ok
test walk_forward_splits_match_golden           ok
test result: ok. 4 passed; 0 failed; finished in 0.00s

=== cargo test 全量 ===
unittests src/lib.rs:      test result: ok. 17 passed
unittests src/main.rs:     test result: ok. 2 passed
tests/golden_test.rs:      test result: ok. 1 passed
tests/indicators_test.rs:  test result: ok. 4 passed
tests/rhai_test.rs:        test result: ok. 2 passed
tests/walk_forward_test.rs: test result: ok. 4 passed
doc-tests:                  (included in lib count)
Total cargo: 34 passed, 0 failed (finished in 1.22s)

=== Python 测试套件 ===
common pytest:           59 passed in 2.86s
stock-assistant pytest: 165 passed in 6.76s
quant-assistant-py:     276 passed, 3 warnings in 19.50s
```

---

## 代码 Review 备注

非阻塞性观察：

1. **算法对齐完整**：`build_walk_forward_windows` 在 doc comment 中逐行引用 Python 等价实现，cursor 起点（`train_size`）、步进逻辑、边界条件与 Python 完全一致。模块级 doc comment 明确声明 bit-identical 设计原则。

2. **文档规范**：`walk_forward.rs` 有模块级 rustdoc（`//!`），三个公开结构体和两个公开函数均有 doc comment；`build_walk_forward_windows` 含 `# Examples`（doctest 可通过）。

3. **链式拼接实现**：`run_walk_forward_ma_backtest` 使用 `current_base * v / window_base` 公式进行复利链式拼接，与 Python `WalkForwardEngine._aggregate` 对齐；第一点等于 `initial_cash` 测试验证了这一性质（误差 < 1e-6）。

4. **边界安全**：实现使用 `usize` 时有下溢防护注释，embargo 逻辑正确（`test_start = train_end + 1 + embargo_size`）；`insufficient_data` 案例（total_rows=20 < 25 = train+embargo+test）产生空窗口，测试验证正确。

5. **范围合规**：未实现参数网格搜索（符合"不做什么"约束），未改动 `run_ma_crossover_backtest`，未添加 HTTP endpoint。

6. **无跨 app import**：`walk_forward.rs` 只 `use crate::run_ma_crossover_backtest`，无跨 app 引用。

7. **golden 文件格式**：4 个案例覆盖 no_embargo/with_embargo/realistic/insufficient_data 场景，tolerance 字段明确标记 abs=0（整数 bit-identical）。

---

## Phase C 进度

- ✅ phaseC.1.rhai（Rhai DSL 引擎接入）
- ✅ phaseC.2.factor.sma（SMA/EMA 指标移植）
- ✅ phaseC.3.walk_forward（本 task）
- ⏳ phaseC.4.onnx
- ⏳ phaseC.5.optimize
- ⏳ phaseC.6.reports
- ⏳ step4.cleanup（删 quant-py）

---

## 后续动作

- ✅ 本 task 可视为已合并（commit `1829c0f` 落 main）
- 更新 `docs/acceptance/INDEX.md`
- 下一步选项：
  - **phaseC.4.onnx**：ONNX 模型推理集成
  - **phaseC.5.optimize**：参数网格搜索（walk-forward 上游已就绪）
