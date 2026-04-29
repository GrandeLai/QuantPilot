# Task phaseF7.token-unlock-panel: TokenUnlockPanel 前端面板

**Phase**: Phase F.7
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/frontends/workbench/src/components/TokenUnlockPanel.tsx`，添加到 `RiskReviewCenter.tsx`。

### UI 设计

- 标题栏 + days 参数选择（7/14/30/60 日）+ 刷新按钮
- **高风险预警区块**（sell_pressure_score ≥ 0.6）
  - 红色卡片列表：协议/代币 / 解锁日期 / 解锁规模 / 抛压分数进度条
- **完整日历区块**（表格）
  - 列：代币 | 协议 | 解锁日期 | 距今（天）| 解锁量（%流通）| 类别 | 抛压评分 | 信号徽章
  - 按 days_until_unlock 升序
- 空态（API 不可用时显示"DefiLlama API 暂时不可达，请稍后重试"）
- dark-theme：`#0E1014` / `#151619` / `#00C087`

---

## 验收标准

- [ ] **AC-1**: 文件存在
  - `test -f apps/stock-assistant/frontends/workbench/src/components/TokenUnlockPanel.tsx`

- [ ] **AC-2**: 注册到 RiskReviewCenter
  - `grep -q "TokenUnlockPanel" apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`

- [ ] **AC-3**: 关键符号存在
  - `grep -q "UnlockCard\|CalendarTable\|TokenUnlockPanel" apps/stock-assistant/frontends/workbench/src/components/TokenUnlockPanel.tsx`

- [ ] **AC-4**: API 客户端函数存在
  - `grep -q "fetchTokenUnlocks\|TokenUnlockCalendar" apps/stock-assistant/frontends/workbench/src/api/client.ts`

- [ ] **AC-5**: TypeScript 编译通过
  - `(cd apps/stock-assistant/frontends/workbench && source ~/.zshrc 2>/dev/null && npm run build)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/frontends/workbench/src/components/TokenUnlockPanel.tsx`

修改：
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`

> **批次开发说明**：F.7.1–F.7.3 在同一工作树批量开发并统一提交。
