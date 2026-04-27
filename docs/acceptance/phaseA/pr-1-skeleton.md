# Acceptance Report: phaseA.pr-1-skeleton

**Run at**: 2026-04-27T12:08:00Z
**Implementation PR/commit**: `28a02e3` — chore: scaffold workspace layout for repo split (Phase A PR 1)
**Diff range**: `dfa3bf2..28a02e3`
**Acceptance-agent invocation**: Bootstrap self-validation（acceptance-agent 在本会话尚未注册）
**Verdict**: ✅ **PASS**

---

## 文件影响范围检查

PR 1 改动文件（23 文件）：
- 新增：`Cargo.toml`、`pyproject.toml`、`package.json`、`package-lock.json`、`uv.lock` ✅ 在白名单内
- 新增：13 个 `.gitkeep` 标记（apps/、common/、tools/、archive/ 子目录）✅ 在白名单内
- 重命名（git rename detection）：`rust_core/{config.toml, Cargo.toml, pyproject.toml, src/lib.rs}` → `apps/quant-assistant/backend/...` ✅ 在白名单内（`rust_core/**` 移除 + `apps/quant-assistant/backend/**` 新增）
- 修改：`.gitignore`（更新 rust_core/target → workspace 根 target/，新增 Cargo.lock 全局忽略）

**结论**：无超出白名单的改动。

注：`Cargo.lock` 在两处出现（workspace 根新生成的、和搬过来的 backend/Cargo.lock）都被新 .gitignore 规则覆盖，所以未进 git。`target/` 同理。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 顶层目录全部存在含 .gitkeep 或文件 | ✅ PASS | 14 个目录全部 `test -d` 通过：apps/{stock-assistant,quant-assistant,quant-assistant-py}, common/{schemas,data-store,parquet,models,golden,frontend-components,python,docs}, tools/{ml-trainer,golden-generator}, archive |
| AC-2: 根 Cargo.toml 含 [workspace] + apps/quant-assistant/backend | ✅ PASS | `grep -A 3 "^\[workspace\]" Cargo.toml` 命中 `apps/quant-assistant/backend` |
| AC-3: 根 pyproject.toml 含 tool.uv 配置 | ✅ PASS | `grep -q "\[tool.uv"` 命中 `[tool.uv.workspace]` 和 `[tool.uv]` |
| AC-4: 根 package.json 含 workspaces 字段 | ✅ PASS | `grep -q "\"workspaces\""` 命中 |
| AC-5: rust_core/ 不存在；apps/quant-assistant/backend/Cargo.toml package = quantpilot-quant | ✅ PASS | `! test -e rust_core` 通过；`grep "name = \"quantpilot-quant\""` 命中 |
| AC-6: `cargo check` 退出码 0 | ✅ PASS | `Checking quantpilot-quant v0.1.0`；`Finished dev profile [unoptimized + debuginfo] target(s) in 14.25s` |
| AC-7: 根 `uv sync` 退出码 0 | ✅ PASS | `Using CPython 3.12.13`、`Resolved 1 package in 13ms`、`Checked in 0.16ms` |
| AC-8: 根 `npm install` 退出码 0 | ✅ PASS | `up to date, audited 1 package in 284ms`、`found 0 vulnerabilities` |

---

## 测试执行日志摘要

```
=== AC-1: dirs exist ===
  apps/stock-assistant: OK
  apps/quant-assistant: OK
  apps/quant-assistant-py: OK
  common/schemas: OK
  common/data-store: OK
  common/data-store/parquet: OK
  common/data-store/models: OK
  common/data-store/golden: OK
  common/frontend-components: OK
  common/python: OK
  common/docs: OK
  tools/ml-trainer: OK
  tools/golden-generator: OK
  archive: OK
=== AC-2: root Cargo.toml workspace === OK
=== AC-3: root pyproject.toml uv config === OK
=== AC-4: root package.json workspaces === OK
=== AC-5: rust_core gone; quant-assistant package name correct ===
  rust_core: removed
  package: quantpilot-quant
=== AC-6: cargo check ===
  ... pyo3 deps compiled ...
  Checking quantpilot-quant v0.1.0
  Finished `dev` profile in 14.25s
=== AC-7: uv sync ===
  Using CPython 3.12.13
  Creating virtual environment at: .venv
  Resolved 1 package in 13ms
  Checked in 0.16ms
=== AC-8: npm install ===
  up to date, audited 1 package in 284ms
  found 0 vulnerabilities
```

---

## 代码 Review 备注

非阻塞性观察：

1. **Rust crate-type 调整**：`rust_core/Cargo.toml` 原本是 `crate-type = ["cdylib"]`（仅 Python 扩展模块）。我改成 `["cdylib", "rlib"]`，让该 crate 同时也能作为普通 Rust 库被引用。Phase B 起 axum 服务会作为 binary 引用此 crate，需要 rlib。当前 PR 1 的 cargo check 通过证明这个改动不破坏现有 PyO3 构建。

2. **`quantpilot_core` → `quantpilot_quant` 改名**：现有 backend 代码库未发现任何 `import quantpilot_core` 调用（早前 codebase 探索结果），改名安全。`backend/tests/test_rust_core.py` 如有引用可能要在 PR 5 移到 quant-assistant-py 时一并更新——记下来供后续注意。

3. **顶层 pyproject.toml 名 `quantpilot-monorepo`** 与 `backend/pyproject.toml` 的 `quantpilot` 区分，避免 uv workspace 解析冲突。后续 PR 4 把 backend → stock-assistant 时 backend/pyproject.toml 一同迁出，监控期内两者并存不冲突（因为 backend/ 不在 workspace members 列表）。

4. **Cargo workspace target/ 位置**：cargo workspace 默认把 target/ 放 workspace 根，不是 member 路径下。我先把 .gitignore 写错了（`apps/quant-assistant/backend/target/`），AC 验证后发现并立即修正为根 `target/` + `Cargo.lock`。

5. **uv.lock + package-lock.json 入 git**：作为 monorepo 锁文件，用于 reproducible builds；Cargo.lock 暂时仍 ignore（package 当前是 cdylib 库形态，按 Rust 习惯库不锁；Phase B 起转 binary 后再考虑入 git）。

6. **`apps/quant-assistant/.gitkeep` 缺**：因该目录已有 backend/ 子目录非空，无需 .gitkeep。

---

## 后续动作

- ✅ 本 PR 可视为已合并（commit `28a02e3` 已落 main）
- 更新 `docs/acceptance/INDEX.md`
- 下一步：进入 PR 2（common/schemas/ + codegen 流水线），见 `docs/tasks/phaseA/pr-2-schemas-codegen.md`
- PR 2 涉及引入 Python 工具（datamodel-codegen）、Rust 工具（typify）、Node 工具（json-schema-to-typescript），需要在 root pyproject.toml 加 `[dependency-groups]` 或 dev deps；同时要写 6 个核心 schema
