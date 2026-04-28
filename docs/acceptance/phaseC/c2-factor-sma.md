# Acceptance Report: phaseC.2.factor.sma

**Run at**: 2026-04-28T04:00:00Z
**Implementation PR/commit**: `7958894` — feat(quant-rust): SMA/EMA indicators + Rhai registration + golden test (Phase C.2)
**Diff range**: commit `7958894` (single commit, 8 files, +875 lines)
**Acceptance-agent invocation**: Manual invocation by user
**Verdict**: ✅ **PASS** — SMA/EMA 指标移植 + Rhai 注册 + golden 等价验证全部通过

---

## 文件影响范围检查

PR 改动 8 文件，全部在白名单内：

- `apps/quant-assistant/backend/src/indicators.rs` ✅（新建）
- `apps/quant-assistant/backend/src/lib.rs` ✅（添加 pub mod indicators）
- `apps/quant-assistant/backend/src/runtime/engine.rs` ✅（注册 sma/ema 函数）
- `apps/quant-assistant/backend/strategies/sma_crossover.rhai` ✅（新建）
- `apps/quant-assistant/backend/tests/indicators_test.rs` ✅（新建）
- `common/data-store/golden/expected/sma_basic.json` ✅（新建）
- `docs/tasks/phaseC/c2-factor-sma.md` ✅（任务规格）
- `tools/golden-generator/src/quantpilot_golden/cases/sma.py` ✅（新建）

无超出白名单。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: `src/indicators.rs` 存在，含 `pub fn sma` 和 `pub fn ema` | ✅ PASS | 文件存在；`grep pub fn sma` 和 `grep pub fn ema` 均命中 |
| AC-2: `lib.rs` 含 `pub mod indicators` | ✅ PASS | `grep pub mod indicators lib.rs` 命中（行 7） |
| AC-3: `runtime/engine.rs` 在 `RhaiEngine::new()` 中注册 `sma` 和 `ema` | ✅ PASS | `register_fn("sma", ...)` 和 `register_fn("ema", ...)` 均存在 |
| AC-4: `strategies/sma_crossover.rhai` 存在，在 Rhai 中调用 `sma()` | ✅ PASS | 文件存在；`fn signal_from_closes` 调用 `sma(closes, fast_period)` |
| AC-5: `common/data-store/golden/expected/sma_basic.json` 存在 | ✅ PASS | 文件存在，含 sma_3/sma_7/ema_3/ema_7 四条序列，tolerance.abs=1e-12 |
| AC-6: `cargo test` 全过（含新增 indicators_test + 已有测试） | ✅ PASS | 25 tests total, 0 failed（13 lib + 2 bin + 1 golden + 4 indicators + 2 rhai + 3 doc）|
| AC-7: `indicators_test::sma_matches_golden` max \|Δ\| < 1e-12 | ✅ PASS | `sma_matches_golden` ok；测试断言 diff < tol（1e-12） |
| AC-8: `indicators_test::ema_matches_golden` max \|Δ\| < 1e-12 | ✅ PASS | `ema_matches_golden` ok；测试断言 diff < tol（1e-12） |
| AC-9: Rhai 中 `sma(closes, period)` 与 Rust `sma()` 结果 bit-equivalent（NaN 映射一致） | ✅ PASS | `rhai_sma_function_matches_rust_sma` ok；测试验证 diff < 1e-12 且 warmup 位置 NaN 对齐 |
| AC-10: 已有测试不受影响（common 59、stock 165、quant-py 276） | ✅ PASS | common 59 passed / stock 165 passed / quant-py 276 passed（3 warnings，无 errors） |

---

## 测试执行日志摘要

```
=== AC-1~AC-5: 文件 & grep 检查 ===
indicators.rs: OK
pub fn sma: OK
pub fn ema: OK
pub mod indicators: OK
sma registered: OK
ema registered: OK
sma_crossover.rhai: OK
sma() call: OK
sma_basic.json: OK

=== cargo test (全量，共 25 tests) ===
unittests src/lib.rs (13 tests):
  indicators::tests::ema_seed_equals_sma_of_first_period     ok
  indicators::tests::ema_rhai_nan_for_warmup                 ok
  indicators::tests::ema_subsequent_values_correct           ok
  indicators::tests::sma_period_1_equals_closes              ok
  indicators::tests::sma_rhai_nan_for_warmup                 ok
  indicators::tests::ema_warmup_is_none                      ok
  indicators::tests::sma_values_correct                      ok
  indicators::tests::sma_warmup_is_none                      ok
  tests::max_drawdown_finds_worst_peak_to_trough             ok
  tests::ma_crossover_with_uptrend_buys_and_holds            ok
  tests::sharpe_near_zero_when_no_volatility                 ok
  runtime::engine::tests::unknown_signal_returns_error       ok
  runtime::engine::tests::rhai_engine_compiles_and_calls_signal  ok
test result: ok. 13 passed

unittests src/main.rs (2 tests):
  healthz_returns_ok_status                                  ok
  root_returns_welcome_message                               ok
test result: ok. 2 passed

tests/golden_test.rs (1 test):
  ma_crossover_basic_matches_python_expected                 ok
test result: ok. 1 passed

tests/indicators_test.rs (4 tests):
  ema_matches_golden                                         ok
  sma_matches_golden                                         ok
  rhai_sma_function_matches_rust_sma                        ok
  rhai_sma_strategy_computes_correct_signals                 ok
test result: ok. 4 passed

tests/rhai_test.rs (2 tests):
  rhai_strategy_path_loads_from_disk                         ok
  rhai_ma_crossover_matches_rust_hardcoded                   ok
test result: ok. 2 passed

doc-tests (3 tests):
  runtime::engine::RhaiEngine usage example                  ok
  indicators::sma doc example                                ok
  indicators::ema doc example                                ok
test result: ok. 3 passed

Total cargo: 25 passed, 0 failed

=== Python 测试套件 ===
common pytest:           59 passed in 2.27s
stock-assistant pytest: 165 passed in 7.31s
quant-assistant-py:     276 passed in 21.16s (3 warnings)
```

---

## 代码 Review 备注

非阻塞性观察：

1. **实现完整度**：`indicators.rs` 实现了 `sma()`/`ema()` 纯 Rust 版（返回 `Vec<Option<f64>>`）和 `sma_rhai()`/`ema_rhai()` Rhai 包装版（返回 `Vec<f64>`，NaN 替代 None）。逻辑清晰，与 task spec 算法描述完全对齐。

2. **文档规范**：`indicators.rs` 有模块级 doc comment，两个公开函数均有完整 rustdoc（含 `# Examples`、`# Panics`、`# Arguments`）；doc-tests 通过验证。符合 Rust doc comment 惯例。

3. **Rhai 注册方式正确**：engine.rs 在 `RhaiEngine::new()` 内通过闭包注册，入参类型为 `rhai::Array + i64`，出参为 `rhai::Array`，与 task spec 约定一致（NaN 替代 None）。

4. **sma_crossover.rhai 设计合理**：新增了 `signal_from_closes(closes, fast_period, slow_period)` 函数（在 Rhai 中调用 `sma()`），同时保留 `signal(fast, slow)` 兼容接口（供原有 `ma_crossover_backtest` 路径使用）。NaN warmup 检查使用 `fast != fast` 惯用法，正确。

5. **golden 文件格式**：`sma_basic.json` 结构完整，包含 case_id、description、input（closes/sma_periods/ema_periods）、expected（sma_3/sma_7/ema_3/ema_7）、tolerance（abs=1e-12）。Python 参考实现（`sma.py`）与 Rust 算法逐行对齐，未引入 pandas-ta 等外部库依赖。

6. **无跨 app import**：`indicators.rs` 不引用 `apps/stock-assistant` 或 `apps/quant-assistant-py` 的任何代码；`common/` 同样未被反向引用。

7. **范围合规**：未实现 RSI/MACD/ATR（符合"不做什么"约束），未改动 `run_ma_crossover_backtest` 逻辑，未添加 HTTP endpoint。

---

## Phase C 进度

- ✅ phaseC.1.rhai（Rhai DSL 引擎接入）
- ✅ phaseC.2.factor.sma（本 task）
- ⏳ phaseC.2.factor.rsi（下一个因子）
- ⏳ phaseC.3.walk_forward
- ⏳ phaseC.4.onnx
- ⏳ phaseC.5.optimize
- ⏳ phaseC.6.reports
- ⏳ step4.cleanup（删 quant-py）

---

## 后续动作

- ✅ 本 task 可视为已合并（commit `7958894` 落 main）
- 更新 `docs/acceptance/INDEX.md`
- 下一步选项：
  - **phaseC.2.factor.rsi**（推荐）：RSI 指标移植，同样模式（Rust + Rhai 注册 + golden + test）
  - **phaseC.3.walk_forward**：walk-forward CV 框架
