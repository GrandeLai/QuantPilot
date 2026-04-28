# Task phaseE.docs-cleanup-refresh: docs/ 整理 + 归档 + 输出最新综合文档

**Phase**: Phase E
**Status**: pending
**Created**: 2026-04-29

---

## 范围

### 背景

`docs/` 顶层混杂了 4 个 Pre-split / Phase 4 时期的文档，引用已删除的模块路径（`backend/src/quantpilot/`、`quantpilot.factors`、`frontend/src/components/`），对当前两 app 结构造成误导。同时缺少功能总结、stock-assistant API 参考、技术实现详细文档。

### 做什么

1. **创建归档区** `docs/archive/legacy/`（含 README 说明归档原因）
2. **归档以下顶层 stale 文档**（移动 + 在归档 README 标注原因）：
   - `docs/Claude_Code_Usage_Guide.md` — Pre-split Phase 0 引导文，引用已不存在的 T-0.1~T-0.4 任务
   - `docs/factor_guide.md` — Phase 4 因子指南，模块 `quantpilot.factors` 已随 quant-assistant-py 删除
   - `docs/llm-agent-layer-design.md` — Pre-split LLM agent 设计，路径 `quantpilot.agent` 已迁至 `quantpilot_stock.agent`
   - `docs/tab-pages-guide.md` — Pre-split 工作台 Tab 说明，引用 `backend/src/quantpilot/`、`frontend/src/components/` 旧路径
3. **保留**（不动）：
   - `docs/quant_tutorial/`（教学内容，技术中立）
   - `docs/superpowers/`（superpowers skill 自动产出，已分隔在子目录）
   - `docs/tasks/`、`docs/acceptance/`（项目协议要求永不删除）
   - `docs/DESIGN.md`、`docs/MIGRATION.md`、`docs/architecture/`、`docs/conventions/`、`docs/protocols/`（已是当前文档）
4. **新增综合文档**：
   - `docs/README.md` — 顶层文档索引
   - `docs/architecture/features.md` — 功能总结（按 app 列出现有能力 + 路由 + 模块）
   - `docs/architecture/tech-stack.md` — 技术实现详解（每层选型 + 关键代码位置）
   - `docs/architecture/stock-assistant-api.md` — stock-assistant Python API 路由参考（与 quant-assistant-api.md 对齐）
   - `docs/archive/README.md` — 归档区索引 + 每个文件归档原因

### 不做什么

- 不修改任何代码
- 不删除任何文件（仅移动到 archive/）
- 不改 docs/quant_tutorial/、docs/superpowers/
- 不重写 DESIGN.md / MIGRATION.md（已是当前状态）

---

## 验收标准

- [ ] **AC-1**: 4 个 stale 文档已从 `docs/` 顶层移除：`test ! -f docs/Claude_Code_Usage_Guide.md && test ! -f docs/factor_guide.md && test ! -f docs/llm-agent-layer-design.md && test ! -f docs/tab-pages-guide.md`
- [ ] **AC-2**: 4 个 stale 文档已搬到 `docs/archive/legacy/`：`test -f docs/archive/legacy/Claude_Code_Usage_Guide.md && test -f docs/archive/legacy/factor_guide.md && test -f docs/archive/legacy/llm-agent-layer-design.md && test -f docs/archive/legacy/tab-pages-guide.md`
- [ ] **AC-3**: `docs/archive/README.md` 存在且为每个归档文件给出归档原因（`grep -c "归档原因\|reason\|Phase 4\|Pre-split" docs/archive/README.md` >= 4）
- [ ] **AC-4**: 4 个新综合文档存在：`docs/README.md`、`docs/architecture/features.md`、`docs/architecture/tech-stack.md`、`docs/architecture/stock-assistant-api.md`
- [ ] **AC-5**: `docs/README.md` 包含到所有顶层 active 文档的链接（`grep -c "DESIGN.md\|MIGRATION.md\|features.md\|tech-stack.md\|quant-assistant-api.md\|stock-assistant-api.md" docs/README.md` >= 6）
- [ ] **AC-6**: `docs/architecture/features.md` 同时覆盖两个 app（`grep -c "stock-assistant\|quant-assistant" docs/architecture/features.md` >= 2）
- [ ] **AC-7**: `docs/architecture/stock-assistant-api.md` 列出至少 10 条路由（`grep -c "^### \(GET\|POST\|PUT\|DELETE\)" docs/architecture/stock-assistant-api.md` >= 10）
- [ ] **AC-8**: `docs/quant_tutorial/`、`docs/tasks/`、`docs/acceptance/` 文件数量未减少（保留协议）

---

## 文件影响范围（白名单）

新建：
- `docs/README.md`
- `docs/archive/README.md`
- `docs/archive/legacy/Claude_Code_Usage_Guide.md`（移动自 `docs/`）
- `docs/archive/legacy/factor_guide.md`（移动自 `docs/`）
- `docs/archive/legacy/llm-agent-layer-design.md`（移动自 `docs/`）
- `docs/archive/legacy/tab-pages-guide.md`（移动自 `docs/`）
- `docs/architecture/features.md`
- `docs/architecture/tech-stack.md`
- `docs/architecture/stock-assistant-api.md`
- `docs/tasks/phaseE/docs-cleanup-refresh.md`（本文件）
- `docs/acceptance/phaseE/docs-cleanup-refresh.md`（acceptance-agent 产出）

删除（实为 git 移动）：
- `docs/Claude_Code_Usage_Guide.md`
- `docs/factor_guide.md`
- `docs/llm-agent-layer-design.md`
- `docs/tab-pages-guide.md`
