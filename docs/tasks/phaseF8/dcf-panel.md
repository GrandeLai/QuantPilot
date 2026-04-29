# Task phaseF8.dcf-panel: DCFPanel 前端面板

**Phase**: Phase F.8
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/frontends/workbench/src/components/DCFPanel.tsx`，添加到 `RiskReviewCenter.tsx`。

### UI 设计

- 标题 + Ticker 输入 + 可配置参数（risk-free rate, terminal growth, projection years）
- **公允价值区块**
  - P5 / P50 / P95 三格展示 + 现价指针
  - Margin of Safety + 估值徽章（deep_value=深绿 / undervalued=绿 / fair=灰 / overvalued=橙 / overheated=红）
  - 5年 FCF 投影折线迷你图（spark chart）
- **WACC 区块**
  - WACC 汇总 + 权益成本 / 债务成本 / 权重明细
- dark-theme：`#0E1014` / `#151619` / `#00C087`

---

## 验收标准

- [ ] **AC-1**: `test -f apps/stock-assistant/frontends/workbench/src/components/DCFPanel.tsx`
- [ ] **AC-2**: `grep -q "DCFPanel" apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
- [ ] **AC-3**: `grep -q "ValuationBand\|WACCSection\|DCFPanel" apps/stock-assistant/frontends/workbench/src/components/DCFPanel.tsx`
- [ ] **AC-4**: `grep -q "fetchDCFValuation\|DCFResultData" apps/stock-assistant/frontends/workbench/src/api/client.ts`
- [ ] **AC-5**: `(cd apps/stock-assistant/frontends/workbench && source ~/.zshrc 2>/dev/null && npm run build)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/frontends/workbench/src/components/DCFPanel.tsx`

修改：
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`

> **批次开发说明**：F.8.1–F.8.3 在同一工作树批量开发并统一提交。
