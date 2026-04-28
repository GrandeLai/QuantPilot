# Task phaseE.workbench-port-residual: 清除 workbench 残余 port 8000 引用

**Phase**: Phase E
**Status**: pending
**Created**: 2026-04-28

---

## 范围

post-b4-docs-sync 修复了 vite.config.ts 代理端口，但发现两处残余引用：

1. `src/api/client.ts:3` — 注释仍写 `8000`
2. `src/components/LiveDataPanel.tsx:67` — WebSocket 默认地址 `ws://localhost:8000`（应为 `ws://localhost:8001`）

### 做什么

- 修正 `api/client.ts` 注释中的端口
- 修正 `LiveDataPanel.tsx` WebSocket 默认端口 8000 → 8001

---

## 验收标准

- [ ] **AC-1**: `grep "8000" apps/stock-assistant/frontends/workbench/src/api/client.ts` 无输出
- [ ] **AC-2**: `grep "8000" apps/stock-assistant/frontends/workbench/src/components/LiveDataPanel.tsx` 无输出
- [ ] **AC-3**: `grep "8001" apps/stock-assistant/frontends/workbench/src/components/LiveDataPanel.tsx` 有输出

---

## 文件影响范围（白名单）

- `apps/stock-assistant/frontends/workbench/src/api/client.ts`
- `apps/stock-assistant/frontends/workbench/src/components/LiveDataPanel.tsx`
- `docs/tasks/phaseE/workbench-port-residual.md`（本文件）
- `docs/acceptance/phaseE/workbench-port-residual.md`（acceptance-agent 产出）
