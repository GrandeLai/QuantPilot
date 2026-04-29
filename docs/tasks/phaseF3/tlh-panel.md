# Task phaseF3.tlh-panel: TLH 前端面板

**Phase**: Phase F.3
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/frontends/workbench/src/components/TLHPanel.tsx`，集成到 `RiskReviewCenter.tsx`。

### UI 结构

```
─── 税务亏损收割（TLH）────────────────────────────────────
⚠ 免责声明：本工具仅供参考，不构成税务建议，请咨询 CPA

[ 输入持仓 Lots ] [ 税率配置 ] [ 扫描 ]

预计节税：$X,XXX

─── 候选仓位 ──────────────────────────────────────────────
[ AAPL × 100 股 ] 亏损 $1,200 (-8.5%) 持有 45 天（短期）
  替代：XLK / VGT
  ⚠ Wash Sale 风险：近 30 天内有买入记录

─── 合规提示 ──────────────────────────────────────────────
• 卖出后 30 天内不得回购同一或 substantially identical 证券
• 推荐先买替代 ETF，30 天后再重新建仓原股
```

---

## 验收标准

- [ ] **AC-1**: 文件存在
  - `test -f apps/stock-assistant/frontends/workbench/src/components/TLHPanel.tsx`

- [ ] **AC-2**: API 调用
  - `grep -q "tlh/scan\|fetchTLH" apps/stock-assistant/frontends/workbench/src/components/TLHPanel.tsx`

- [ ] **AC-3**: 集成进 RiskReviewCenter
  - `grep -q "TLHPanel" apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`

- [ ] **AC-4**: dark-theme tokens
  - `grep -q "#0E1014\|#151619\|#00C087" apps/stock-assistant/frontends/workbench/src/components/TLHPanel.tsx`

- [ ] **AC-5**: 免责声明存在
  - `grep -q "不构成税务建议\|CPA\|disclaimer" apps/stock-assistant/frontends/workbench/src/components/TLHPanel.tsx`

- [ ] **AC-6**: type-check + build 通过
  - `(cd apps/stock-assistant/frontends/workbench && env -u GVM_ROOT npm run type-check)` 退出码 0
  - `(cd apps/stock-assistant/frontends/workbench && env -u GVM_ROOT npm run build)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/frontends/workbench/src/components/TLHPanel.tsx`

修改：
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`

> **批次开发说明**：F.3.1–F.3.5 在同一工作树批量开发并统一提交。验收时须在 clean working tree（`git diff HEAD` 为空）下执行，避免未提交的兄弟任务文件触发误报。
