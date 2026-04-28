# Task phaseC.2.factor.sma: SMA 指标移植 + Rhai 注册 + golden 等价验证

**Phase**: C
**Status**: in-progress
**Created**: 2026-04-28
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 做什么

- 新建 `src/indicators.rs`：
  - `pub fn sma(closes: &[f64], period: usize) -> Vec<Option<f64>>`：SMA（简单移动平均）
    - 索引 `i < period-1`：`None`（warmup 期）
    - 索引 `i >= period-1`：`Some(mean(closes[i-period+1..=i]))`
  - `pub fn ema(closes: &[f64], period: usize) -> Vec<Option<f64>>`：EMA（指数移动平均）
    - 第一个有效值 = SMA(closes[0..period])
    - 后续：`ema[i] = closes[i] * k + ema[i-1] * (1 - k)`，其中 `k = 2.0 / (period + 1) as f64`
- 在 `lib.rs` 添加 `pub mod indicators;`
- 在 `RhaiEngine::new()` 中注册 `sma` 和 `ema` 为 Rhai 原生函数：
  - `sma(closes: Vec<f64>, period: i64) -> Vec<f64>`（Rhai 无 Option，NaN 替代 None）
  - `ema(closes: Vec<f64>, period: i64) -> Vec<f64>`（同上，NaN 替代 None）
- 新建 `strategies/sma_crossover.rhai`：展示在 Rhai 中直接调用 `sma()` 计算快慢线并生成信号
- 新建 `tools/golden-generator/src/quantpilot_golden/cases/sma.py`：
  - `python_sma(closes, period) -> list[float | None]`：与 Rust 逐行对齐
  - `python_ema(closes, period) -> list[float | None]`：与 Rust 逐行对齐
  - `generate_sma_basic()`：用 25 根固定 K 线生成 SMA/EMA golden case
- 新建 `common/data-store/golden/expected/sma_basic.json`
- 新建 `apps/quant-assistant/backend/tests/indicators_test.rs`：
  - `sma_matches_golden`：Rust sma() vs golden expected（max |Δ| < 1e-12）
  - `ema_matches_golden`：Rust ema() vs golden expected（max |Δ| < 1e-12）
  - `rhai_sma_strategy_computes_correct_signals`：加载 sma_crossover.rhai，验证信号序列
  - `rhai_sma_function_matches_rust_sma`：Rhai 内调用 sma() 与 Rust 直接调用结果 bit-equivalent

### 不做什么

- 不删除 quant-py 的 `/indicators/calculate` 端点（全量清理留 Step 4）
- 不实现 RSI/MACD/ATR（留后续 C.2.factor.rsi 等）
- 不改变 `run_ma_crossover_backtest` 逻辑（那个用的是内联 SMA，不改）
- 不添加 HTTP endpoint `/indicators/sma`（API 层留 C.2.1.b 或合并进后续）

---

## 验收标准

- [ ] **AC-1**: `src/indicators.rs` 存在，含 `pub fn sma` 和 `pub fn ema`
- [ ] **AC-2**: `lib.rs` 含 `pub mod indicators`
- [ ] **AC-3**: `runtime/engine.rs` 在 `RhaiEngine::new()` 中注册了 `sma` 和 `ema` 函数
- [ ] **AC-4**: `strategies/sma_crossover.rhai` 存在，在 Rhai 中调用 `sma()` 计算信号
- [ ] **AC-5**: `common/data-store/golden/expected/sma_basic.json` 存在
- [ ] **AC-6**: `cargo test` 全过（含新增 indicators_test + 已有测试）
- [ ] **AC-7**: `indicators_test::sma_matches_golden` max |Δ| < 1e-12
- [ ] **AC-8**: `indicators_test::ema_matches_golden` max |Δ| < 1e-12
- [ ] **AC-9**: Rhai 中 `sma(closes, period)` 与 Rust `sma()` 结果 bit-equivalent（NaN 映射一致）
- [ ] **AC-10**: 已有测试不受影响（common 59、stock 165、quant-py 276）

---

## 测试集合

```bash
# AC-1
test -f apps/quant-assistant/backend/src/indicators.rs
grep -q "pub fn sma" apps/quant-assistant/backend/src/indicators.rs
grep -q "pub fn ema" apps/quant-assistant/backend/src/indicators.rs

# AC-2
grep -q "pub mod indicators" apps/quant-assistant/backend/src/lib.rs

# AC-3
grep -q "sma" apps/quant-assistant/backend/src/runtime/engine.rs

# AC-4
test -f apps/quant-assistant/backend/strategies/sma_crossover.rhai
grep -q "sma(" apps/quant-assistant/backend/strategies/sma_crossover.rhai

# AC-5
test -f common/data-store/golden/expected/sma_basic.json

# AC-6 + AC-7 + AC-8 + AC-9
(cd apps/quant-assistant/backend && cargo test 2>&1 | grep "test result")
(cd apps/quant-assistant/backend && cargo test --test indicators_test 2>&1 | grep -q "test result: ok")

# AC-10
(cd common/python && uv run --group dev pytest tests/ -q | tail -2 | grep -q "59 passed")
(cd apps/stock-assistant/backend && uv run pytest tests/ -q | tail -2 | grep -q "165 passed")
(cd apps/quant-assistant-py/backend && uv run pytest tests/ -q | tail -2 | grep -q "276 passed")
```

---

## 文件影响范围（白名单）

```
- apps/quant-assistant/backend/src/indicators.rs (新建)
- apps/quant-assistant/backend/src/lib.rs
- apps/quant-assistant/backend/src/runtime/engine.rs
- apps/quant-assistant/backend/strategies/sma_crossover.rhai (新建)
- apps/quant-assistant/backend/tests/indicators_test.rs (新建)
- common/data-store/golden/expected/sma_basic.json (新建)
- tools/golden-generator/src/quantpilot_golden/cases/sma.py (新建)
- docs/tasks/phaseC/c2-factor-sma.md (本文件)
```

---

## 引用

- **设计来源**：plan §5 "C.x.indicators: 在 Rhai engine 注册 sma/ema/rsi/atr 等"，plan §9 "phaseC.2.factor.<name>"
- **上游依赖**：phaseC.1.rhai（RhaiEngine 已实现）
- **下游依赖**：phaseC.2.factor.rsi（下一个指标），phaseC.4.onnx（ML推理）
