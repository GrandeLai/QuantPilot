# Task phaseC.1.rhai: Rhai DSL engine + 第一个用户策略 + cross-impl equivalence

**Phase**: C
**Status**: passed
**Implementation PR**: commit `3761e88`
**Acceptance**: [docs/acceptance/phaseC/c1-rhai.md](../../acceptance/phaseC/c1-rhai.md) — ✅ PASS (2026-04-28)
**Created**: 2026-04-28
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 做什么

- 在 `apps/quant-assistant/backend/Cargo.toml` 添加 `rhai` crate 作为依赖
- 新建 `src/runtime/mod.rs` + `src/runtime/engine.rs`：
  - `RhaiEngine`：包装 `rhai::Engine`
  - `compile_strategy(path) -> CompiledStrategy`：从文件读 + 编译
  - `call_signal(strategy, fast_ma, slow_ma) -> Signal`：调用策略 `signal(fast, slow)` 函数
  - `Signal` enum: `Long / Flat / Hold`（最简化 MVP；后续 C.x 扩 strength 等）
- 新建 `strategies/ma_crossover.rhai`：示例 Rhai 策略，定义 `fn signal(fast, slow) -> string` 返回 `"long"|"flat"|"hold"`
- 在 `lib.rs` 添加 `pub mod runtime;` 暴露
- 新建 `pub fn run_rhai_ma_crossover_backtest(closes, strategy_path, fast_period, slow_period, initial_cash) -> Result<Vec<f64>, String>`：与 `run_ma_crossover_backtest` 算法相同，但**通过 Rhai 调用决定方向**（Rust 算 sma，Rhai 决定 long/flat/hold）
- 新建集成测试 `tests/rhai_test.rs`：
  - 加载 `strategies/ma_crossover.rhai`，跑同样的 25 根 K 线数据
  - 断言 Rhai 驱动版的 equity_curve 与 Rust 硬编码版一致（max |Δ| < 1e-12）
  - 这证明 Rhai 引擎不引入数值误差

### 不做什么

- 不实现完整的 `on_bar(bar, state)` Rhai DSL（带状态/订单系统）—— 那是 C.x 后续
- 不在 Rhai 中暴露 sma/ema 等指标函数（Rust 算好后传 fast/slow 进去）—— 后续 C.2 加
- 不删除 `quant-py.strategy.loader`（它仍服务 Python templates 加载；Step 4 时整体删 quant-py）
- 不在 `/backtest` HTTP 端点暴露策略选择参数 —— 留给 phaseC.1.b 或 C.2
- 不接 ONNX（C.4）

---

## 验收标准

- [ ] **AC-1**: Cargo.toml 含 `rhai` 依赖
- [ ] **AC-2**: `apps/quant-assistant/backend/strategies/ma_crossover.rhai` 存在，含 `fn signal(fast, slow)`
- [ ] **AC-3**: `src/runtime/engine.rs` 提供 `RhaiEngine::compile_strategy()` 和 `call_signal()`
- [ ] **AC-4**: `lib.rs` 暴露 `pub mod runtime` 和 `pub fn run_rhai_ma_crossover_backtest`
- [ ] **AC-5**: `cargo test` 全过（lib + bin + golden + 新增 rhai test）
- [ ] **AC-6**: `tests/rhai_test.rs` 测试 Rhai 驱动 MA crossover 与 Rust 硬编码版 equity_curve 等价（max |Δ| < 1e-12）
- [ ] **AC-7**: 其它测试不受影响（common 59、stock 165、quant-py 276）
- [ ] **AC-8**: golden test 仍过（前两个 task 的产出未破坏）

---

## 测试集合

```bash
# AC-1
test -f apps/quant-assistant/backend/Cargo.toml
grep -q "^rhai" apps/quant-assistant/backend/Cargo.toml

# AC-2
test -f apps/quant-assistant/backend/strategies/ma_crossover.rhai
grep -q "fn signal" apps/quant-assistant/backend/strategies/ma_crossover.rhai

# AC-3
test -f apps/quant-assistant/backend/src/runtime/engine.rs

# AC-4
grep -q "pub mod runtime" apps/quant-assistant/backend/src/lib.rs
grep -q "pub fn run_rhai_ma_crossover_backtest" apps/quant-assistant/backend/src/lib.rs

# AC-5
(cd apps/quant-assistant/backend && cargo test 2>&1 | grep "test result")

# AC-6 + AC-8
(cd apps/quant-assistant/backend && cargo test --test rhai_test 2>&1 | grep -q "test result: ok")
(cd apps/quant-assistant/backend && cargo test --test golden_test 2>&1 | grep -q "test result: ok")

# AC-7
(cd common/python && uv run --group dev pytest tests/ -q | tail -2 | grep -q "59 passed")
(cd apps/stock-assistant/backend && uv run pytest tests/ -q | tail -2 | grep -q "165 passed")
(cd apps/quant-assistant-py/backend && uv run pytest tests/ -q | tail -2 | grep -q "276 passed")
```

---

## 文件影响范围（白名单）

```
- apps/quant-assistant/backend/Cargo.toml
- apps/quant-assistant/backend/src/lib.rs
- apps/quant-assistant/backend/src/runtime/mod.rs (新建)
- apps/quant-assistant/backend/src/runtime/engine.rs (新建)
- apps/quant-assistant/backend/strategies/ma_crossover.rhai (新建)
- apps/quant-assistant/backend/tests/rhai_test.rs (新建)
```

---

## 引用

- **设计来源**：plan §5 "策略 DSL 选型: Rhai + native trait registry（混合）" + Phase C.1
- **上游依赖**：phaseB.mvp.backtest（Rust /backtest 已工作）
- **下游依赖**：phaseC.1.b（暴露策略选择给 /backtest HTTP）或 C.2（因子库移植）
