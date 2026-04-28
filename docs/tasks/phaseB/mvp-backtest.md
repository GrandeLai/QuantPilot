# Task phaseB.mvp.backtest: Rust /backtest endpoint + cross-language equivalence

**Phase**: B
**Status**: passed
**Implementation PR**: commit `6c3c8de`
**Acceptance**: [docs/acceptance/phaseB/mvp-backtest.md](../../acceptance/phaseB/mvp-backtest.md) — ✅ PASS (2026-04-28)
**Created**: 2026-04-27
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 做什么

- Rust 端：实现 `POST /backtest` 端点（axum），接受 BacktestRequest JSON，返回 BacktestResponse JSON
- 算法：MA crossover（已在 `lib.rs` 中实现）+ sharpe + max_drawdown
- Python 端：在 `tools/golden-generator/` 实现一个**与 Rust lib.rs 逐行对齐**的 Python MA crossover 算法（不是 quant-py 的 BaseStrategy 引擎，那个含 fees/slippage 不同），命名 `python_ma_crossover_backtest`
- Cross-language equivalence 测试：
  - `tools/golden-generator/cases/ma_crossover.py` 用一组固定 closes 跑出 expected 输出，写入 `common/data-store/golden/expected/ma_crossover_basic.json`
  - Rust 集成测试 `apps/quant-assistant/backend/tests/golden_test.rs`：读同样 closes，跑 Rust `run_ma_crossover_backtest`，对比 expected，最大绝对差 < 1e-12
- `tools/golden-generator/cli.py` 的 `generate` 命令实际生效（不再仅打占位）

### 不做什么

- 不实现 DuckDB 读取（下个 task；本 task closes 直接走 JSON body）
- 不接 Polars（pure Rust f64 vec 即够）
- 不实现 schemas 中的完整 BacktestConfig（只用最小 BacktestRequest）
- 不接 Rhai DSL（phaseC.1）
- 不集成 quant-py 的 BacktestEngine（含手续费、StrategyContext 等，与 Rust 简单算法不一致；本 task 只对齐"裸 MA crossover 逻辑"）

---

## 验收标准

- [ ] **AC-1**: `POST /backtest` 端点存在；请求体 JSON `{symbol, closes:[f64], fast_period, slow_period, initial_cash}` 返回 200 + `{equity_curve, total_return, sharpe_ratio, max_drawdown}`
- [ ] **AC-2**: Rust `cargo test` 全过（含新增的 backtest_endpoint test 和 golden test）
- [ ] **AC-3**: `tools/golden-generator/` 的 `generate --case-id ma_crossover_basic` 成功跑通，写入 `common/data-store/golden/expected/ma_crossover_basic.json`
- [ ] **AC-4**: Rust 集成测试读 expected，跑 Rust impl，最大绝对差 < 1e-12
- [ ] **AC-5**: 端到端 curl 验证：启 binary，curl 同样 input，与 expected 对比 < 1e-12
- [ ] **AC-6**: 其它测试不受影响（common 59、stock 165、quant-py 276、Phase B 已有测试 5）
- [ ] **AC-7**: 如果 Rust 算法与 Python 实现存在差异，记录在 acceptance 报告备注里（不阻塞 PASS，但要有解释）

---

## 测试集合

```bash
# AC-1: backtest endpoint with sample input
/Users/bytedance/code/QuantPilot/target/debug/quantpilot-quant-server &
sleep 2
RESPONSE=$(curl -sS -X POST http://localhost:8002/backtest \
  -H 'Content-Type: application/json' \
  -d '{"symbol":"TEST","closes":[100,101,102,103,99,98,100,105,107,110,112,108,106,104,102,100,98,99,101,103,105,107,109,111,113],"fast_period":3,"slow_period":7,"initial_cash":10000}')
echo "$RESPONSE" | grep -q '"equity_curve"' && echo "AC-1: OK"
pkill -f quantpilot-quant-server

# AC-2: cargo test
(cd apps/quant-assistant/backend && cargo test 2>&1 | tail -3)

# AC-3: golden generator runs
uv run --package quantpilot-golden golden-generator generate --case-id ma_crossover_basic
test -f common/data-store/golden/expected/ma_crossover_basic.json

# AC-4: Rust integration test reads expected and matches
(cd apps/quant-assistant/backend && cargo test --test golden_test 2>&1 | grep -q "test result: ok")

# AC-6: other tests
(cd common/python && uv run --group dev pytest tests/ -q | tail -2 | grep -q "59 passed")
(cd apps/stock-assistant/backend && uv run pytest tests/ -q | tail -2 | grep -q "165 passed")
(cd apps/quant-assistant-py/backend && uv run pytest tests/ -q | tail -2 | grep -q "276 passed")
```

---

## 文件影响范围（白名单）

```
- apps/quant-assistant/backend/Cargo.toml (添加 reqwest? 不需要; serde 已有)
- apps/quant-assistant/backend/src/main.rs (添加 POST /backtest 路由)
- apps/quant-assistant/backend/tests/golden_test.rs (新建集成测试)
- tools/golden-generator/src/quantpilot_golden/cli.py
- tools/golden-generator/src/quantpilot_golden/cases/__init__.py (新建)
- tools/golden-generator/src/quantpilot_golden/cases/ma_crossover.py (新建)
- common/data-store/golden/expected/ma_crossover_basic.json (新建)
- common/data-store/golden/manifest.json (新建/更新)
```

---

## 引用

- **设计来源**：plan §5 "Phase B 起步范围 (MVP)" + §7 "跨语言行为等价测试"
- **上游依赖**：phaseB.mvp.healthz
- **下游依赖**：phaseC.1.rhai（Rhai 策略 + 真实多策略支持）
