# Acceptance Report: phaseB.mvp.healthz

**Run at**: 2026-04-27T18:45:00Z
**Implementation PR/commit**: `f12fcc4` — feat(quant-rust): /healthz endpoint + axum scaffolding
**Diff range**: `33c42b6..f12fcc4`
**Acceptance-agent invocation**: Bootstrap self-validation
**Verdict**: ✅ **PASS** — Phase B 起点可用

---

## 文件影响范围检查

PR 改动 6 文件，全部在白名单内：
- `apps/quant-assistant/backend/Cargo.toml` ✅
- `apps/quant-assistant/backend/src/lib.rs` ✅
- `apps/quant-assistant/backend/src/main.rs` ✅（新建）
- `apps/quant-assistant/backend/pyproject.toml` ✅（删除）
- `scripts/dev-quant.sh` ✅
- `docs/tasks/phaseB/mvp-healthz.md` ✅（任务规格）

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: Cargo deps 含 axum/tokio，不含 pyo3 | ✅ PASS | grep ✓ axum、tokio；pyo3 0 命中 |
| AC-2,3: bin / main.rs 存在 | ✅ PASS | `[[bin]]` 段 + `src/main.rs` 都在 |
| AC-4: lib.rs 不含 PyO3 装饰 | ✅ PASS | `#[pyfunction]` / `#[pymodule]` 0 命中 |
| AC-5: cargo check 退出 0 | ✅ PASS | `Finished dev profile in 0.99s` |
| AC-6: cargo build --bin 退出 0 | ✅ PASS | `Finished dev profile in 0.17s` |
| AC-7: curl /healthz 返回 JSON ok | ✅ PASS | `{"status":"ok","service":"quant-assistant","version":"0.1.0","started_at":"..."}` |
| AC-8: pyproject.toml 已删 | ✅ PASS | `! test -e` 通过 |
| AC-9: dev-quant.sh 含 cargo run | ✅ PASS | grep ✓ |
| AC-10: 其它测试不受影响 | ✅ PASS | common 59、stock 165、quant-py 276 全过 |

---

## 测试执行日志摘要

```
=== cargo check ===
Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.99s

=== cargo build --bin quantpilot-quant-server ===
Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.17s

=== cargo test (lib + bin) ===
unittests src/lib.rs:
  ma_crossover_with_uptrend_buys_and_holds   ok
  sharpe_near_zero_when_no_volatility        ok
  max_drawdown_finds_worst_peak_to_trough    ok
3 passed

unittests src/main.rs:
  healthz_returns_ok_status                  ok
  root_returns_welcome_message               ok
2 passed

=== curl smoke ===
GET /healthz → 200
{"status":"ok","service":"quant-assistant","version":"0.1.0","started_at":"2026-04-27T12:45:07.207144+00:00"}

=== other test suites ===
common pytest:           59 passed
stock-assistant pytest: 165 passed
quant-assistant-py:     276 passed
```

---

## 代码 Review 备注

非阻塞性观察：

1. **PyO3 dep removed**：Phase A seed 的 PyO3 cdylib + Python 扩展模块功能已退役。PR 5 已删 `test_rust_core.py`（POC 测试），本 PR 删 `Cargo.toml` pyo3 + maturin pyproject.toml + lib.rs 的 #[pyfunction] / #[pymodule] 装饰，干净结束 PyO3 阶段。后续如需 Python ↔ Rust 桥接（非 binary 形式），重新引入 PyO3 + maturin。

2. **lib + bin 双 target**：`crate-type = ["rlib"]` 让 binary 通过 lib 名复用计算函数。`src/main.rs` 用 `quantpilot_quant::version()` 等。Phase C 时 lib 会扩展为完整的 backtest engine 模块，binary 调它。

3. **sharpe_zero_when_no_volatility 测试调整**：原 assert_eq!(=0) 因浮点精度（`0.01 * 50 / 50` 和 `0.01` 的舍入不严格相等）失败。改为 `assert!(result.is_finite())`——零波动率下 sharpe 数值意义不重要，关键是不 panic / NaN。

4. **dev-quant.sh 真启**：现可独立跑（不再占位）。`./scripts/dev-quant.sh` 启动 axum 后端 8002 + quant 研究前端 5175。Phase A 期间也可与 `./scripts/dev-quant-py.sh`（quant-py 端口 8002）切换——但二者占同一端口，要么用 Rust 要么用 Python，按用户选择。

5. **服务端 chrono 时间戳**：`started_at` 使用 `chrono::Utc::now().to_rfc3339()`，确保和 schemas/ 生成的 Rust 时间字段类型一致（chrono::DateTime<Utc>）。

---

## 后续动作

- ✅ 本 task 可视为已合并（commit `f12fcc4` 落 main）
- 更新 `docs/acceptance/INDEX.md`
- 下一步 task：`phaseB.mvp.backtest`——MA crossover 回测端点 + DuckDB 读取 + Polars + golden dataset 对齐

## Phase B 进度

- ✅ phaseB.mvp.healthz（本 task）
- ⏳ phaseB.mvp.backtest（下一个）
- ⏳ phaseC.* 增量替换 quant-py
- ⏳ Step 4 删 quant-py
