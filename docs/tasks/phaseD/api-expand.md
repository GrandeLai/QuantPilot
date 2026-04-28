# Task phaseD.api-expand: 扩展 quant-assistant HTTP API

**Phase**: Phase D
**Status**: in-progress
**Created**: 2026-04-28
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

Phase B/C 已实现 Rust 量化库（indicators、walk_forward、optimizer、reports、ml_runner、runtime）及基础 HTTP 端点（GET /healthz、POST /backtest）。Phase D 将所有库能力通过标准 HTTP API 对外暴露，并重构为 `src/api/` 模块结构。

### 做什么

1. **添加 trade tracking** 到 MA crossover 回测：记录每笔交易（entry/exit 价格、PnL、胜负）
2. **重构 `src/main.rs`** → `src/api/mod.rs` + 子模块（keep main.rs 仅含启动代码）
3. **升级 `POST /api/backtest/run`**（原 `/backtest`）：
   - 接受 OHLCV bars 数组（含 `close`、`time` 字段）
   - 返回完整 BacktestResult（含 trade 统计：win_rate、profit_factor、total_trades 等）
   - MA crossover 策略参数通过 `strategy_params` 传入
4. **新增 `POST /api/walk-forward`**：调用 `walk_forward::run_walk_forward_ma_backtest`
5. **新增 `POST /api/optimize`**：调用 `optimizer::grid_search_ma_crossover`，返回 top-N 参数组合
6. **新增 `POST /api/indicators`**：接受 closes + indicator type（sma/ema）+ period，返回序列
7. **更新 `GET /`**：列出全部 API 端点
8. **保留 `GET /healthz`**（不变）
9. **在 `main.rs` 中注册所有路由**（`src/api/` 提供 `pub fn router() -> Router`）

### 不做什么

- 不做 DuckDB 集成（市场数据仍由调用方传入）
- 不做 ML 推理 HTTP 端点（留 Phase D.2）
- 不做 Rhai HTTP 端点（留 Phase D.2）
- 不改 common/ 或 stock-assistant/

---

## 验收标准

- [ ] **AC-1**: `src/api/` 目录存在，main.rs 仅含启动逻辑（`build_app()` 调 `api::router()`）
- [ ] **AC-2**: `POST /api/backtest/run` 接受 `bars`（含 `close` 字段）+ `fast_period` + `slow_period` + `initial_cash`，返回含 `metrics.total_return`、`metrics.sharpe_ratio`、`metrics.win_rate`、`metrics.total_trades` 的 JSON
- [ ] **AC-3**: `POST /api/walk-forward` 接受 `closes`/`fast_period`/`slow_period`/`initial_cash`/walk-forward 配置，返回 `n_windows`、`equity_curve`
- [ ] **AC-4**: `POST /api/optimize` 接受 `closes`/`initial_cash`/`fast_periods`/`slow_periods`，返回按 Sharpe 排序的参数列表
- [ ] **AC-5**: `POST /api/indicators` 接受 `closes`/`indicator`(`sma`|`ema`)/`period`，返回 `values` 数组
- [ ] **AC-6**: `cargo test` 全过（无 FAILED）
- [ ] **AC-7**: `GET /` 返回的 `endpoints` 列表包含 `/api/backtest/run`、`/api/walk-forward`、`/api/optimize`、`/api/indicators`

---

## 测试集合

```bash
# AC-6
(cd apps/quant-assistant/backend && cargo test 2>&1 | grep "test result" | grep -v "FAILED")

# AC-2 (端到端 curl 测试，服务运行后)
# curl -s -X POST http://localhost:8002/api/backtest/run \
#   -H "Content-Type: application/json" \
#   -d '{"symbol":"TEST","bars":[{"close":100},{"close":101},...], "fast_period":3,"slow_period":7,"initial_cash":10000}' \
#   | jq '.metrics.total_return'

# 单元 + 集成测试（在 tests/ 目录）
(cd apps/quant-assistant/backend && cargo test api 2>&1 | tail -5)
```

---

## 文件影响范围（白名单）

```
新建：
- apps/quant-assistant/backend/src/api/mod.rs
- apps/quant-assistant/backend/src/api/backtest.rs
- apps/quant-assistant/backend/src/api/indicators.rs
- apps/quant-assistant/backend/src/api/optimize.rs
- apps/quant-assistant/backend/src/api/walk_forward.rs
  注：各模块内嵌 #[cfg(test)] 测试（Rust 惯用写法），不新建独立 tests/api_test.rs

修改：
- apps/quant-assistant/backend/src/main.rs  （精简为启动逻辑）
- apps/quant-assistant/backend/src/lib.rs   （添加 Trade/TradeStats 及 run_ma_crossover_backtest_with_stats）
- apps/quant-assistant/backend/src/optimizer.rs（为 OptimizeResult 添加 Serialize，API 层编译所需）

文档（同步新建）：
- docs/tasks/phaseD/api-expand.md（本文件）
- docs/tasks/phaseE/frontend-wired.md（Phase E 任务预写）
```

---

## 引用

- **计划**：plan §5 "Phase B起步范围" + "Phase C 增量替换路线"
- **前置**：phaseB.mvp.backtest PASS，phaseC.1-C.6 PASS，step4.cleanup PASS
