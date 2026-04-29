# Task phaseF6.eps-revision-panel: EPSRevisionPanel 前端面板

**Phase**: Phase F.6
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/frontends/workbench/src/components/EPSRevisionPanel.tsx`，添加到 `RiskReviewCenter.tsx`。

### UI 设计

- 标题栏 + Ticker 输入 + 查询按钮
- **修正动量区块**（每个期间一行）
  - 期间标签（本季度 / 下季度 / 本年度 / 明年度）
  - 7 日：↑N / ↓N → 修正分数进度条
  - 30 日：↑N / ↓N → 修正分数进度条
  - 方向徽章（strong_upgrade=深绿 / upgrade=浅绿 / neutral=灰 / downgrade=橙 / strong_downgrade=红）
- **目标价共识区块**
  - 平均/中位/高/低目标价
  - 上行空间（upside %）进度条
- 整体方向总评徽章
- dark-theme：`#0E1014` / `#151619` / `#00C087`

---

## 验收标准

- [ ] **AC-1**: 文件存在
  - `test -f apps/stock-assistant/frontends/workbench/src/components/EPSRevisionPanel.tsx`

- [ ] **AC-2**: 注册到 RiskReviewCenter
  - `grep -q "EPSRevisionPanel" apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`

- [ ] **AC-3**: 关键符号存在
  - `grep -q "RevisionRow\|TargetSection\|EPSRevisionPanel" apps/stock-assistant/frontends/workbench/src/components/EPSRevisionPanel.tsx`

- [ ] **AC-4**: API 客户端函数存在
  - `grep -q "fetchEpsRevisionSummary\|EpsRevisionMomentum" apps/stock-assistant/frontends/workbench/src/api/client.ts`

- [ ] **AC-5**: TypeScript 编译通过
  - `(cd apps/stock-assistant/frontends/workbench && source ~/.zshrc 2>/dev/null && npm run build)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/frontends/workbench/src/components/EPSRevisionPanel.tsx`

修改：
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`

> **批次开发说明**：F.6.1–F.6.3 在同一工作树批量开发并统一提交。
