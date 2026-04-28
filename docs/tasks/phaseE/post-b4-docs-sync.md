# Task phaseE.post-b4-docs-sync: B4 完工后文档同步 + workbench 端口修复

**Phase**: Phase E (post-B4)
**Status**: pending
**Created**: 2026-04-28
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

Phase E 完工后（A1–A3 + B1 + B4）发现以下遗漏：

1. **`apps/stock-assistant/frontends/workbench/vite.config.ts`** 代理目标端口写死为 `8000`，但 stock-assistant 后端标准端口为 `8001`（CLAUDE.md、dev-stock.sh 均如此），导致工作台开发模式下 API 调用全部 404。
2. **`docs/architecture/frontend-routing.md`** 缺少 `/api/ml` → 8002 代理行（A3 添加了该路由但文档未同步），且 workbench proxy 表仍显示 8000。
3. **`docs/DESIGN.md`** 路线图缺 B4（mypy 类型覆盖）条目。
4. **`docs/MIGRATION.md`** 缺少 A1–A3 + B1 + B4 的迁移记录。

### 做什么

1. **修复 workbench vite.config.ts**：`8000` → `8001`
2. **更新 frontend-routing.md**：
   - workbench proxy 表 8000 → 8001，移除"Warning: stale port"注释
   - quant-assistant proxy 表添加 `/api/ml` → 8002 行
3. **更新 DESIGN.md 路线图**：添加 B4 条目（✅ 完成）
4. **追加 MIGRATION.md**：添加 A1–A3 + B1 + B4 迁移记录段

### 不做什么

- 不修改 stock-assistant 后端代码
- 不修改 quant-assistant Rust 后端
- 不修改 quant-assistant 前端 vite.config.ts（已正确）

---

## 验收标准

- [ ] **AC-1**: `grep "8000" apps/stock-assistant/frontends/workbench/vite.config.ts` 无输出（端口已改）
- [ ] **AC-2**: `grep "8001" apps/stock-assistant/frontends/workbench/vite.config.ts` 有输出
- [ ] **AC-3**: `grep "api/ml" docs/architecture/frontend-routing.md` 有输出
- [ ] **AC-4**: `grep "B4\|mypy" docs/DESIGN.md` 有输出
- [ ] **AC-5**: `grep "B4\|mypy" docs/MIGRATION.md` 有输出
- [ ] **AC-6**: `(cd apps/stock-assistant/frontends/workbench && npm run build)` 无错误退出

---

## 文件影响范围（白名单）

修改：
- `apps/stock-assistant/frontends/workbench/vite.config.ts`
- `docs/architecture/frontend-routing.md`
- `docs/DESIGN.md`
- `docs/MIGRATION.md`

新建：
- `docs/tasks/phaseE/post-b4-docs-sync.md`（本文件）
- `docs/acceptance/phaseE/post-b4-docs-sync.md`（acceptance-agent 产出）
