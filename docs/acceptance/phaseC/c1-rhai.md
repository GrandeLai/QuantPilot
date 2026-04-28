# Acceptance Report: phaseC.1.rhai

**Run at**: 2026-04-28T03:30:00Z
**Implementation PR/commit**: `3761e88` — feat(quant-rust): Rhai DSL engine + first user strategy
**Diff range**: `b262d63..3761e88`
**Acceptance-agent invocation**: Bootstrap self-validation
**Verdict**: ✅ **PASS** — Rhai 策略 DSL 引擎 + 第一个用户策略接入

---

## 文件影响范围检查

PR 改动 7 文件，全部在白名单内：
- `apps/quant-assistant/backend/Cargo.toml` ✅（添加 rhai 依赖）
- `apps/quant-assistant/backend/src/lib.rs` ✅（添加 pub mod runtime + run_rhai_ma_crossover_backtest）
- `apps/quant-assistant/backend/src/runtime/mod.rs` ✅（新建，re-export）
- `apps/quant-assistant/backend/src/runtime/engine.rs` ✅（新建 RhaiEngine 封装）
- `apps/quant-assistant/backend/strategies/ma_crossover.rhai` ✅（新建首个 .rhai 策略）
- `apps/quant-assistant/backend/tests/rhai_test.rs` ✅（新建集成测试）
- `docs/tasks/phaseC/c1-rhai.md` ✅（任务规格）

无超出白名单。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: Cargo deps 含 rhai | ✅ PASS | `grep ^rhai Cargo.toml` 命中 |
| AC-2: ma_crossover.rhai 含 fn signal | ✅ PASS | 文件存在；`grep "fn signal"` 命中 |
| AC-3: src/runtime/engine.rs 提供 RhaiEngine + compile_strategy + call_signal | ✅ PASS | 文件存在；含 RhaiEngine、CompiledStrategy、Signal 三类型 |
| AC-4: lib.rs 暴露 runtime 模块 + run_rhai_ma_crossover_backtest | ✅ PASS | grep 两条命中 |
| AC-5: cargo test 全过 | ✅ PASS | 11 passed (5 lib + 2 bin + 1 golden + 2 rhai + 1 doc) |
| AC-6: rhai_test 等价测试 < 1e-12 | ✅ PASS | `rhai_ma_crossover_matches_rust_hardcoded` ok；max \|Δ\| 实测在 1e-12 容差内 |
| AC-7: 其它测试不受影响 | ✅ PASS | common 59、stock 165、quant-py 276 全过 |
| AC-8: golden test 仍过 | ✅ PASS | `golden_test::ma_crossover_basic_matches_python_expected` ok |

---

## 测试执行日志摘要

```
=== cargo test (full) ===
unittests src/lib.rs:
  ma_crossover_with_uptrend_buys_and_holds         ok
  sharpe_near_zero_when_no_volatility              ok
  max_drawdown_finds_worst_peak_to_trough          ok
  runtime::engine::tests::rhai_engine_compiles_and_calls_signal  ok
  runtime::engine::tests::unknown_signal_returns_error  ok
test result: ok. 5 passed

unittests src/main.rs (bin):
  healthz_returns_ok_status                        ok
  root_returns_welcome_message                     ok
test result: ok. 2 passed

tests/golden_test.rs:
  ma_crossover_basic_matches_python_expected       ok
test result: ok. 1 passed

tests/rhai_test.rs:
  rhai_ma_crossover_matches_rust_hardcoded         ok
  rhai_strategy_path_loads_from_disk               ok
test result: ok. 2 passed

doc-tests:
  runtime::engine::RhaiEngine usage example        ok
test result: ok. 1 passed

Total: 11 cargo tests, all green

=== other test suites ===
common pytest:           59 passed
stock-assistant pytest: 165 passed
quant-assistant-py:     276 passed
```

---

## 代码 Review 备注

非阻塞性观察：

1. **MVP 范围意图**：Phase C.1 故意限定为"Rhai 引擎 + 一个 signal 函数"，避开了完整的 on_bar/on_init/state DSL。理由：
   - 立即建立"Rhai 不引入数值误差"的事实（通过 cross-impl equivalence test）
   - 让后续 task 在该基础上演进而不是一次性做完整 DSL
   - 用户可以从最简单的 `fn signal(fast, slow)` 开始写策略；后续扩展是增量的

2. **Rhai DSL 与 Rust 决策路径完全相同**：
   - `run_ma_crossover_backtest`（Rust 硬编码）：`if fast > slow && position == 0 && cash > 0 { buy }`
   - `run_rhai_ma_crossover_backtest`：Rust 算 fast/slow → Rhai signal(fast, slow) → Rust match Signal → 同样的 buy/sell 逻辑
   - 集成测试断言两者 equity_curve bit-equivalent（max |Δ| < 1e-12）—— 实测全相同

3. **rhai feature flag**：选 "sync"，因为 axum handler 需要 Send。如未来引入 async Rhai 调用（C.x），可能换成 default 或 "sync_async"。

4. **Strategy DSL 路线图**（plan §5 Phase C.x 中扩展）：
   - C.1（当前）：fn signal(fast, slow) -> string
   - C.x.indicators：在 Rhai engine 注册 sma/ema/rsi/atr 等 → 用户可在 .rhai 中调
   - C.x.state：增加 state map (positions, cash, recent_trades) 传给 fn on_bar(bar, state)
   - C.x.orders：return rich Signal { action, strength, reason } 替代 string
   - C.4.onnx：在 Rhai 中暴露 ml_predict("model_id", feature_vec) → ONNX 推理

5. **Quant-py 的 strategy.loader 暂未删**：
   - 它仍服务 stock-assistant/api/portfolio.py 的 lazy import（在 stock-assistant 的 `try: from quantpilot_quant.strategy.loader ...` 包装内）
   - 当 Rhai 替代 quant-py 全部策略加载能力后（C.x 完整 DSL + 用户策略持久化在 stock 这边），quant-py.strategy.loader 才能真正删除
   - Step 4 时整体删 quant-py，到时这个 loader 自然消失

6. **Rhai 编译错误处理**：`compile_file` 错误被映射成 String，当前足够清晰（含 path）。Phase C.x 时可加专门的 `RhaiCompileError` enum（thiserror），让 axum handler 把编译错误转 422 响应。

---

## 后续动作

- ✅ 本 task 可视为已合并（commit `3761e88` 落 main）
- 更新 `docs/acceptance/INDEX.md`
- 下一步选项：
  - **C.1.b**（推荐）：把 strategy 选择暴露给 `/backtest` HTTP 端点（增 strategy_id query 参数；默认 hardcoded，传 "rhai:ma_crossover" 走 Rhai 路径）
  - **C.2**：因子库逐个移植（移 sma/ema/rsi/macd 进 Rust，并在 Rhai 中暴露）
  - **C.3**：walk-forward CV
- 或暂停、做其他事

## Phase C 进度

- ✅ phaseC.1.rhai（本 task）
- ⏳ phaseC.2.factor.<name> （因子库移植，按因子粒度分若干 PR）
- ⏳ phaseC.3.walk_forward
- ⏳ phaseC.4.onnx
- ⏳ phaseC.5.optimize
- ⏳ phaseC.6.reports
- ⏳ step4.cleanup（删 quant-py）
