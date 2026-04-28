# Acceptance Report: phaseB.mvp.backtest

**Run at**: 2026-04-28T03:00:00Z
**Implementation PR/commit**: `6c3c8de` — feat(quant-rust): /backtest endpoint + cross-language equivalence
**Diff range**: `b97b6e9..6c3c8de`
**Acceptance-agent invocation**: Bootstrap self-validation
**Verdict**: ✅ **PASS** — Rust quant-assistant 第一个实际算法端点 + 跨语言等价基准就位

---

## 文件影响范围检查

PR 改动 7 文件，全部在白名单内：
- `apps/quant-assistant/backend/src/main.rs` ✅（添加 POST /backtest）
- `apps/quant-assistant/backend/tests/golden_test.rs` ✅（新建集成测试）
- `tools/golden-generator/src/quantpilot_golden/cli.py` ✅（generate 实际生效）
- `tools/golden-generator/src/quantpilot_golden/cases/__init__.py` ✅（新建）
- `tools/golden-generator/src/quantpilot_golden/cases/ma_crossover.py` ✅（新建，对齐 Rust 算法）
- `common/data-store/golden/expected/ma_crossover_basic.json` ✅（首个 golden 期望文件）
- `docs/tasks/phaseB/mvp-backtest.md` ✅（任务规格）

无超出白名单。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: POST /backtest 端点 + JSON in/out | ✅ PASS | curl 返回 200 + equity_curve/sharpe/max_drawdown |
| AC-2: cargo test 全过 | ✅ PASS | 6/6: 3 lib + 2 bin + 1 integration |
| AC-3: golden generator 写出 expected | ✅ PASS | `ma_crossover_basic.json` 生成成功 |
| AC-4: Rust 集成测试与 expected 对齐 | ✅ PASS | golden_test 内最大 abs diff 1.819e-12 < 容差 1e-9 |
| AC-5: 端到端 curl ↔ expected 等价 | ✅ PASS | max \|Δ equity\| = 0.000e+00; sharpe diff = 2.220e-16 |
| AC-6: 其它测试不受影响 | ✅ PASS | common 59、stock 165、quant-py 276 全过 |
| AC-7: 算法差异说明 | ✅ N/A | 算法逐行对齐；差异仅来自浮点 summation 顺序的 ~2 ULP，已记录 |

---

## 测试执行日志摘要

```
=== AC-1: HTTP endpoint smoke ===
POST /backtest with 25-bar input
{
  "symbol": "TEST",
  "fast_period": 3, "slow_period": 7, "initial_cash": 10000,
  "equity_curve": [10000, ..., 10181.81, 9818.18, ..., 9792.69],
  "total_return": -0.0207...,
  "sharpe_ratio": -1.27...,
  "max_drawdown": 0.0727..., max_drawdown_start: 10, max_drawdown_end: 14
}

=== AC-2: cargo test all ===
running 3 tests (lib)        ok
running 2 tests (bin/main)   ok
running 1 test (golden_test) ok

=== AC-3: golden generator ===
✓ ma_crossover_basic → common/data-store/golden/expected/ma_crossover_basic.json

=== AC-4: integration test ===
test ma_crossover_basic_matches_python_expected ... ok
  max |Δ equity| = 1.819e-12 (within 1e-9 tolerance)

=== AC-5: end-to-end ===
HTTP /backtest output vs golden expected:
  max |Δ equity| = 0.000e+00
  sharpe diff    = 2.220e-16  (1 ULP)
  max_dd diff    = 0.000e+00

=== AC-6: other tests ===
common: 59 passed
stock-assistant: 165 passed
quant-assistant-py: 276 passed
```

---

## 代码 Review 备注

非阻塞性观察：

1. **Rust ↔ Python 浮点等价**：
   - 集成测试中 `golden_test.rs` 看到 1.819e-12 abs diff（一处 9446.049277824975 vs 9446.049277824977）
   - 端到端 curl ↔ expected 是 0.000e+00（HTTP serde 走整数计算路径稍微不同？或者更可能：integration test 在 cargo 进程启动时算，HTTP 在另一个进程算，但最终落到 IEEE 754 双精度的同一个结果）
   - sharpe ratio 差 2.220e-16 = 1 ULP，最佳可能
   - 1e-9 tolerance 给的是 1000 倍 headroom，符合 plan §7"equity_curve abs=1e-9"

2. **没用 Polars 也没用 DuckDB**：
   - MA crossover 是简单算法，f64 vec 充分；引入 Polars 会增加~50MB 依赖且对此 case 无收益
   - DuckDB 集成是下一个 task 的事——本 task 主要建立"跨语言等价测试 pattern"
   - 未来 phaseC.2.factor.* 移植因子时再加 Polars

3. **golden-generator CLI 真生效**：
   - PR 7 时只是 stub；本 task 的 case logic 让 `generate --case-id ma_crossover_basic` 实际写文件
   - `verify-python` 让 Python 端自己检查"内部 stable"——重跑 case 与已存在 expected 比对
   - manifest.json 还没建（plan §7 提到的多 case 索引）；当前只一个 case，单文件 JSON 自描述够

4. **Python 算法逐行对齐 Rust**：
   - `python_ma_crossover_backtest` 不是 quant-py 的 BaseStrategy 引擎调用——后者带 fees/slippage/StrategyContext 抽象，与 Rust 简单算法对不上
   - 本 task 用一个**专门镜像 Rust 的 Python**，作为跨语言等价的"对照参考"
   - Phase C 时 quant-py 的 BacktestEngine 移到 Rust 时，golden-generator 会有自己的"对照 Python 实现"以保证迁移正确

5. **下个 task 的栈**：
   - phaseB.mvp.backtest（本 task）：纯 closes 数组 → equity ✓
   - 下一步要么是 DuckDB 接入（phaseB.mvp.data-loader 或 phaseC.0.duckdb）：从 market.duckdb 读 OHLCV
   - 要么是 phaseC.1.rhai（Rhai 策略 DSL）—— 但需要先有"backtest can run a strategy" 抽象，这又依赖 BaseStrategy-like trait
   - Phase B 已基本就位（HTTP shell + 一个工作 endpoint + golden 流程）；Phase C 是真正的功能搬迁

---

## 后续动作

- ✅ 本 task 可视为已合并（commit `6c3c8de` 落 main）
- 更新 `docs/acceptance/INDEX.md`
- Phase B MVP **完工**——核心 pattern（axum + golden-driven equivalence）建立
- 下一步：进入 Phase C 增量替换；或先做 Phase B 收尾（DuckDB 读 + 多 case manifest + 更多 golden 测试）

## Phase B 总结

| Task | 状态 | 关键贡献 |
|---|---|---|
| phaseB.mvp.healthz | ✅ | axum binary + 退役 PyO3 seed + /healthz |
| phaseB.mvp.backtest | ✅ | /backtest + Rust ↔ Python golden 等价基准 + tools/golden-generator 实际工作 |

Phase B "MVP" 范围已覆盖。Phase C 起增量替换 quant-py 各模块（Rhai/factors/walk_forward/ONNX/optimize/reports）。
