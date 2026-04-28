# Acceptance Report: phaseD.api-expand

**Run at**: 2026-04-28T09:00:00Z
**Implementation PR**: commit 7b5a2f0167a047388f94be86a35db2937a312378
**Diff range**: `a470368..7b5a2f0`
**Acceptance-agent invocation**: claude-sonnet-4-6 (2026-04-28)
**Verdict**: ✅ PASS (v2 — task spec 白名单已更新补全 optimizer.rs 及文档文件)

**v1 Verdict**: NEEDS-REVISION（白名单文档遗漏）

---

## 文件影响范围检查

改动文件总数：10

在白名单内：7
- `apps/quant-assistant/backend/src/api/backtest.rs` (新建)
- `apps/quant-assistant/backend/src/api/indicators.rs` (新建)
- `apps/quant-assistant/backend/src/api/mod.rs` (新建)
- `apps/quant-assistant/backend/src/api/optimize.rs` (新建)
- `apps/quant-assistant/backend/src/api/walk_forward.rs` (新建)
- `apps/quant-assistant/backend/src/lib.rs` (修改)
- `apps/quant-assistant/backend/src/main.rs` (修改)

超出白名单：3
- `apps/quant-assistant/backend/src/optimizer.rs`：添加 `use serde::Serialize;` 和 `#[derive(Serialize)]` 到 `OptimizeResult` 结构体。内容**必要**——`/api/optimize` 端点需要序列化 `OptimizeResult`，缺少此 derive 会导致编译失败。属于 spec 白名单遗漏，非"顺手重构"。建议将此文件加入白名单。
- `docs/tasks/phaseD/api-expand.md`：此文件在本 commit 中首次创建（之前不存在）。按流程规范，task spec 应在实现**之前**创建。此为过程偏差，内容本身正确。
- `docs/tasks/phaseE/frontend-wired.md`：新建下一阶段 task spec。纯增量，与本 task 无关，不影响功能。

**白名单缺失文件**：
- `apps/quant-assistant/backend/tests/api_test.rs`：白名单列出"新建"但实际未创建。测试改以 `#[cfg(test)]` 内联模块方式写入各 `src/api/*.rs` 文件，共 6 个 API 测试全部通过。为 Rust 惯用做法，测试编写要求已满足，非跳过测试。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: `src/api/` 目录存在，main.rs 仅含启动逻辑（`build_app()` 调 `api::router()`） | ✅ PASS | `src/api/` 目录存在含 mod.rs + 4 子模块。`main.rs` 仅保留 `healthz()`、`root()`（全局端点）、`build_app()`（调 `quantpilot_quant::api::router()`）和 `main()`。路由合并通过 `.merge(quantpilot_quant::api::router())`。 |
| AC-2: `POST /api/backtest/run` 接受 `bars`（含 `close` 字段）+ `fast_period` + `slow_period` + `initial_cash`，返回含 `metrics.total_return`、`metrics.sharpe_ratio`、`metrics.win_rate`、`metrics.total_trades` 的 JSON | ✅ PASS | `src/api/backtest.rs` 定义 `BacktestRunRequest`（含 `bars: Vec<Bar>`，`Bar` 有 `close: f64` 字段）和 `BacktestRunResponse`（含 `metrics: BacktestMetrics`，含所有4个字段）。测试 `backtest_run_returns_metrics` 验证返回值存在并为数字类型，退出码 0。 |
| AC-3: `POST /api/walk-forward` 接受 `closes`/`fast_period`/`slow_period`/`initial_cash`/walk-forward 配置，返回 `n_windows`、`equity_curve` | ✅ PASS | `src/api/walk_forward.rs` 定义 `WalkForwardRequest`（含 `closes`, `fast_period`, `slow_period`, `initial_cash`, `train_size`, `test_size`, `step_size`, `embargo_size`）和 `WalkForwardResponse`（含 `n_windows`, `equity_curve`）。测试 `walk_forward_returns_windows` 验证响应包含 `n_windows > 0` 和 `equity_curve` 数组，退出码 0。 |
| AC-4: `POST /api/optimize` 接受 `closes`/`initial_cash`/`fast_periods`/`slow_periods`，返回按 Sharpe 排序的参数列表 | ✅ PASS | `src/api/optimize.rs` 定义 `OptimizeRequest`（含全部4字段）和 `OptimizeResponse`（含 `results: Vec<OptimizeResult>`）。调用 `grid_search_ma_crossover` 返回按 Sharpe 降序排列结果。测试 `optimize_returns_sorted_results` 验证排序正确性，退出码 0。 |
| AC-5: `POST /api/indicators` 接受 `closes`/`indicator`(`sma`\|`ema`)/`period`，返回 `values` 数组 | ✅ PASS | `src/api/indicators.rs` 定义 `IndicatorsRequest`（含 `closes`, `indicator: IndicatorType { Sma, Ema }`, `period`）和 `IndicatorsResponse`（含 `values: Vec<Option<f64>>`）。两个测试分别验证 SMA 和 EMA，均通过，退出码 0。 |
| AC-6: `cargo test` 全过（无 FAILED） | ✅ PASS | 59 tests passed, 0 failed（见测试执行日志）。 |
| AC-7: `GET /` 返回的 `endpoints` 列表包含 `/api/backtest/run`、`/api/walk-forward`、`/api/optimize`、`/api/indicators` | ✅ PASS | `main.rs` `root()` 函数中 `endpoints` 数组包含所有4个路径。测试 `root_lists_all_endpoints` 用字符串断言验证，通过，退出码 0。 |

---

## 测试执行日志摘要

### `cargo test 2>&1 | grep "test result"`

退出码：0

关键输出：
```
test result: ok. 31 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.02s
test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.02s
test result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 2 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.01s
test result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
test result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 4 filtered out; finished in 2.07s
```

合计：59 tests, 0 failed。

### `cargo test api 2>&1 | grep -E "^running|test result"`

退出码：0

关键输出：
```
running 6 tests
test result: ok. 6 passed; 0 failed; ...
```

6 个 API 测试（2 backtest + 1 walk_forward + 1 optimize + 2 indicators）全部通过。

---

## 代码 Review 备注

1. **`optimizer.rs` Serialize 添加**：仅添加了 `use serde::Serialize;` 和 `#[derive(Serialize)]` 到 `OptimizeResult`。改动最小化，无副作用，功能必要。
2. **`ApiError` 类型在3个子模块中重复定义**：`backtest.rs`、`walk_forward.rs`、`optimize.rs`、`indicators.rs` 各自定义了相同的 `pub struct ApiError(pub StatusCode, pub String)` 和相同的 `IntoResponse` 实现。建议后续在 `api/mod.rs` 中提取共享类型，但不阻塞当前 AC（无 AC 要求代码 DRY）。
3. **task spec 和下一阶段 spec 同一 commit 提交**：按流程规范，task spec 应在实现前独立提交（"没有 task spec 不动手"）。本次 spec 与实现代码在同一 commit 中，属过程偏差。任务功能完整，后续遵守此流程即可。
4. **`tests/api_test.rs` 未创建**：白名单列出该文件但实现选择内联 `#[cfg(test)]` 模块。Rust 项目两种方式均合法，且6个 API 测试实际存在并通过。

---

## 后续动作

本次 verdict = NEEDS-REVISION，原因是3个文件超出白名单（`optimizer.rs`、`docs/tasks/phaseD/api-expand.md`、`docs/tasks/phaseE/frontend-wired.md`）。建议用户决断：

**开放问题**：
1. 是否接受将 `apps/quant-assistant/backend/src/optimizer.rs` 补充进白名单？（推荐：是，因为该改动是功能必须的，属 spec 遗漏）
2. 是否接受 `docs/tasks/phaseD/api-expand.md` 和 `docs/tasks/phaseE/frontend-wired.md` 在同一 commit 中创建的过程偏差？（推荐：是，内容正确，过程偏差轻微）
3. 是否接受以内联 `#[cfg(test)]` 模块替代 `tests/api_test.rs`？（推荐：是，Rust 惯用法，测试已覆盖全部端点）

若用户对以上3点均接受，可直接升级 verdict 为 PASS 并合 PR。若需修复，implementation-agent 应：
- 更新 task spec 白名单增加 `optimizer.rs`
- 不需要修改代码（功能和测试均满足所有 AC）
