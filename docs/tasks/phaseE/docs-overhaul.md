# Task phaseE.docs-overhaul: Phase A–E 文档全面更新

**Phase**: Phase E
**Status**: pending
**Created**: 2026-04-28
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

Phase A–E 已完成（monorepo 拆分 + Rust 量化后端 + API 模块化 + 前端接线），但大多数文档仍反映 Phase A 或拆分前状态。本任务将所有核心文档对齐到当前实现状态。

### 做什么

1. **更新 `docs/DESIGN.md`**：完整重写，反映 Phase A–E 双产品结构
2. **更新 `README.md`**：反映当前 monorepo 布局，删除对旧 backend/、rust_core/ 的引用
3. **更新 `CLAUDE.md`**：添加 Phase D 四个端点、确认 quant 前端端口 5175
4. **追加 `docs/MIGRATION.md`**：Step 4（quant-py 删除）+ Phase D + Phase E
5. **小改 `docs/protocols/duckdb-write-discipline.md`**：添加 results.duckdb 说明
6. **小改 `docs/conventions/acceptance-process.md`**：NEEDS-REVISION 解决路径说明
7. **新建 `docs/architecture/quant-assistant-api.md`**：Rust 5 个端点完整参考
8. **新建 `docs/architecture/frontend-routing.md`**：Vite proxy 路由表

### 不做什么

- 不改任何代码
- 不改验收工具（acceptance-agent）
- 不覆盖已有验收记录

---

## 验收标准

- [ ] **AC-1**: `grep -r "quant-assistant-py\|rust_core\|apps/backend" docs/ README.md CLAUDE.md` 在 MIGRATION.md 之外无命中（MIGRATION.md 中的引用是历史记录，允许）
- [ ] **AC-2**: `test -f docs/architecture/quant-assistant-api.md` 且文件包含 `/api/backtest/run`、`/api/walk-forward`、`/api/optimize`、`/api/indicators`、`/healthz`（`grep -c "api/" docs/architecture/quant-assistant-api.md` >= 4）
- [ ] **AC-3**: `test -f docs/architecture/frontend-routing.md` 且文件包含 `8001` 和 `8002`
- [ ] **AC-4**: `grep -c "api/backtest\|api/walk-forward\|api/optimize\|api/indicators" CLAUDE.md` >= 4
- [ ] **AC-5**: `grep -c "apps/stock-assistant\|apps/quant-assistant" docs/DESIGN.md` >= 2 且 `grep -c "8001\|8002" docs/DESIGN.md` >= 2

---

## 文件影响范围（白名单）

修改：
- docs/DESIGN.md
- README.md
- CLAUDE.md
- docs/MIGRATION.md
- docs/protocols/duckdb-write-discipline.md
- docs/conventions/acceptance-process.md

新建：
- docs/tasks/phaseE/docs-overhaul.md（本文件）
- docs/architecture/quant-assistant-api.md
- docs/architecture/frontend-routing.md
- docs/acceptance/phaseE/docs-overhaul.md（验收记录，acceptance-agent 产出）
