# Task phaseB.mvp.healthz: Rust quant-assistant /healthz endpoint + axum scaffolding

**Phase**: B
**Status**: pending
**Implementation PR**: <pending>
**Created**: 2026-04-27
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 做什么
- 把 `apps/quant-assistant/backend/` 从 PyO3 cdylib seed 改造为 axum binary
- 移除 PyO3 依赖（Phase A seed 不再使用；Python 测试已删 in PR 5）
- `Cargo.toml`：换为 rlib + bin 双 target；deps 加 axum / tokio / serde / serde_json / anyhow / tracing / tracing-subscriber / chrono
- `src/lib.rs`：保留 math 函数（version, run_ma_crossover_backtest, sharpe_ratio, max_drawdown）但**去除 #[pyfunction] / #[pymodule] 装饰**——成为普通 Rust 库
- 新建 `src/main.rs`：axum 应用入口
- 实现 `GET /healthz`：返回 JSON `{status, service, version, started_at}`，端口 8002
- 删除 `apps/quant-assistant/backend/pyproject.toml`（maturin 配置，不再需要）
- 更新 `scripts/dev-quant.sh`：从占位脚本变成真正起 axum 服务

### 不做什么
- 不实现 `/backtest` 端点（下一个 task: `phaseB.mvp.backtest`）
- 不接 DuckDB（下一个 task）
- 不启用 Polars（下一个 task）
- 不删除 quant-py（Step 4 的事；Phase B 期间并存）
- 不改 `apps/quant-assistant/backend/.cargo/config.toml`（如有）

---

## 验收标准

- [ ] **AC-1**: `apps/quant-assistant/backend/Cargo.toml` 含 `axum` 和 `tokio` 作为依赖；不含 `pyo3`
- [ ] **AC-2**: `apps/quant-assistant/backend/Cargo.toml` 含 `[[bin]]` 段或 `src/main.rs` 存在
- [ ] **AC-3**: `apps/quant-assistant/backend/src/main.rs` 存在并定义 axum app
- [ ] **AC-4**: `apps/quant-assistant/backend/src/lib.rs` 不再含 `#[pyfunction]` 或 `#[pymodule]`
- [ ] **AC-5**: `cd apps/quant-assistant/backend && cargo check` 退出码 0
- [ ] **AC-6**: `cd apps/quant-assistant/backend && cargo build --bin <bin-name>` 退出码 0（产生 binary）
- [ ] **AC-7**: 启动 binary 后 `curl http://localhost:8002/healthz` 返回 200 + JSON 含 `status: "ok"`、`service: "quant-assistant"`
- [ ] **AC-8**: `apps/quant-assistant/backend/pyproject.toml` 已删除（不再 maturin 构建）
- [ ] **AC-9**: `scripts/dev-quant.sh` 真正调 `cargo run` 启动服务（不再占位）
- [ ] **AC-10**: 其它 app 测试不受影响（common 59、stock 165、quant-py 276 全过）

---

## 测试集合

```bash
# AC-1
test -f apps/quant-assistant/backend/Cargo.toml
grep -q "^axum" apps/quant-assistant/backend/Cargo.toml
grep -q "^tokio" apps/quant-assistant/backend/Cargo.toml
! grep -q "^pyo3" apps/quant-assistant/backend/Cargo.toml

# AC-2,3
test -f apps/quant-assistant/backend/src/main.rs

# AC-4
! grep -E "#\[pyfunction\]|#\[pymodule\]" apps/quant-assistant/backend/src/lib.rs

# AC-5
(cd apps/quant-assistant/backend && cargo check)

# AC-6
(cd apps/quant-assistant/backend && cargo build --bin quantpilot-quant-server)

# AC-7: 启动 binary，curl，shutdown
(cd apps/quant-assistant/backend && cargo run --bin quantpilot-quant-server &) && \
  sleep 2 && \
  curl -s http://localhost:8002/healthz | grep -q '"status":"ok"' && \
  curl -s http://localhost:8002/healthz | grep -q '"service":"quant-assistant"' && \
  pkill -f quantpilot-quant-server

# AC-8
! test -e apps/quant-assistant/backend/pyproject.toml

# AC-9
grep -q "cargo run" scripts/dev-quant.sh

# AC-10
(cd common/python && uv run --group dev pytest tests/ -q | tail -2 | grep -q "59 passed")
(cd apps/stock-assistant/backend && uv run pytest tests/ -q | tail -2 | grep -q "165 passed")
(cd apps/quant-assistant-py/backend && uv run pytest tests/ -q | tail -2 | grep -q "276 passed")
```

---

## 文件影响范围（白名单）

```
- apps/quant-assistant/backend/Cargo.toml
- apps/quant-assistant/backend/Cargo.lock (gitignored，不进 git)
- apps/quant-assistant/backend/src/lib.rs
- apps/quant-assistant/backend/src/main.rs (新建)
- apps/quant-assistant/backend/pyproject.toml (删除)
- scripts/dev-quant.sh
- docs/acceptance/phaseB/.gitkeep (建目录)
```

---

## 引用

- **设计来源**：plan §5（Rust quant-assistant 内部架构）+ "Phase B 起步范围 (MVP)"
- **上游依赖**：Phase A 全部 PR PASS
- **下游依赖**：phaseB.mvp.backtest（接 DuckDB + Polars + 实际 backtest 端点）
