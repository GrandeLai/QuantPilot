# Task phaseF9.short-interest-panel: ShortInterestPanel 前端面板

**Phase**: Phase F.9
**Status**: pending
**Created**: 2026-04-29

---

## UI 设计

- 标题 + Ticker 输入 + 批量扫描（逗号分隔）
- **单票详情**：short_pct_float 进度条 / days-to-cover 进度条 / 轧空风险评分 / MoM 变化
- **批量扫描结果表格**：按 squeeze_risk_score 降序

---

## 验收标准

- [ ] **AC-1**: `test -f apps/stock-assistant/frontends/workbench/src/components/ShortInterestPanel.tsx`
- [ ] **AC-2**: `grep -q "ShortInterestPanel" apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
- [ ] **AC-3**: `grep -q "SqueezeGauge\|ScanTable\|ShortInterestPanel" apps/stock-assistant/frontends/workbench/src/components/ShortInterestPanel.tsx`
- [ ] **AC-4**: `grep -q "fetchShortInterest\|ShortInterestData" apps/stock-assistant/frontends/workbench/src/api/client.ts`
- [ ] **AC-5**: `(cd apps/stock-assistant/frontends/workbench && source ~/.zshrc 2>/dev/null && npm run build)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/frontends/workbench/src/components/ShortInterestPanel.tsx`

修改：
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`

> **批次开发说明**：F.9.1–F.9.3 在同一工作树批量开发并统一提交。
