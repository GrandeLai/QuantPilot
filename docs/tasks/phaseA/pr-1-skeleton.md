# Task phaseA.pr-1-skeleton: 仓库 layout 骨架

**Phase**: A
**Status**: pending
**Implementation PR**: <pending>
**Created**: 2026-04-27
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 做什么
- 创建顶层目录结构（含 `.gitkeep`）：
  - `apps/{stock-assistant,quant-assistant,quant-assistant-py}/`
  - `common/{schemas,data-store,frontend-components,python,docs}/`
  - `common/data-store/{parquet,models,golden}/`
  - `tools/{ml-trainer,golden-generator}/`
  - `archive/`
- 创建根级 workspace 配置：
  - `Cargo.toml`（workspace member: `apps/quant-assistant/backend`）
  - `pyproject.toml`（uv workspace 顶层；members 在子任务中加入）
  - 根 `package.json`（workspaces: `apps/stock-assistant/frontends/*`、`apps/quant-assistant/frontend`、`common/frontend-components`；初期 members 可不存在）
- **整体移动 `rust_core/` → `apps/quant-assistant/backend/`**：保留作为 Phase B 起点种子；调整 Cargo.toml 中 package name 改为 `quantpilot-quant`，更新内部路径

### 不做什么
- 不移动 Python 后端代码（PR 3-5）
- 不移动前端代码（PR 6）
- 不写任何 schema（PR 2）
- 不创建启动脚本（PR 7）

---

## 验收标准

- [ ] **AC-1**: 以下顶层目录存在且都包含 `.gitkeep` 或实际文件：`apps/stock-assistant/`、`apps/quant-assistant/`、`apps/quant-assistant-py/`、`common/schemas/`、`common/data-store/`、`common/data-store/parquet/`、`common/data-store/models/`、`common/data-store/golden/`、`common/frontend-components/`、`common/python/`、`common/docs/`、`tools/ml-trainer/`、`tools/golden-generator/`、`archive/`
- [ ] **AC-2**: 根 `Cargo.toml` 存在且声明 `[workspace]` + `members = ["apps/quant-assistant/backend"]`
- [ ] **AC-3**: 根 `pyproject.toml` 存在并使用 uv workspace 配置（即使 members 此 PR 后还是空也可，但语法合法）
- [ ] **AC-4**: 根 `package.json` 存在并声明 `"workspaces"` 字段
- [ ] **AC-5**: `rust_core/` 顶层目录已不存在；`apps/quant-assistant/backend/Cargo.toml` 存在且 package name = `quantpilot-quant`
- [ ] **AC-6**: `cd apps/quant-assistant/backend && cargo check` 退出码 0
- [ ] **AC-7**: 根 `uv sync` 退出码 0（即使 workspace member 为空）
- [ ] **AC-8**: 根 `npm install` 退出码 0

---

## 测试集合

```bash
# AC-1
for d in apps/stock-assistant apps/quant-assistant apps/quant-assistant-py \
         common/schemas common/data-store common/data-store/parquet \
         common/data-store/models common/data-store/golden \
         common/frontend-components common/python common/docs \
         tools/ml-trainer tools/golden-generator archive; do
  test -d "$d" || (echo "MISSING DIR: $d" && exit 1)
done

# AC-2
test -f Cargo.toml
grep -A 5 "^\[workspace\]" Cargo.toml | grep -q "apps/quant-assistant/backend"

# AC-3
test -f pyproject.toml
grep -q "tool.uv" pyproject.toml || grep -q "tool.uv.workspace" pyproject.toml

# AC-4
test -f package.json
grep -q "\"workspaces\"" package.json

# AC-5
! test -e rust_core
test -f apps/quant-assistant/backend/Cargo.toml
grep -q "name = \"quantpilot-quant\"" apps/quant-assistant/backend/Cargo.toml

# AC-6
cd apps/quant-assistant/backend && cargo check
cd ../../..

# AC-7
uv sync

# AC-8
npm install
```

---

## 文件影响范围（白名单）

```
- Cargo.toml (新建)
- pyproject.toml (顶层新建；现有 backend/pyproject.toml 不动)
- package.json (新建)
- apps/**/.gitkeep
- common/**/.gitkeep
- tools/**/.gitkeep
- archive/.gitkeep
- apps/quant-assistant/backend/** (来自 rust_core/ 整体移动)
- rust_core/** (移除)
```

---

## 引用

- **设计来源**：plan §4 PR 1
- **上游依赖**：phaseA.pr-0-cleanup
- **下游依赖**：phaseA.pr-2-schemas-codegen
