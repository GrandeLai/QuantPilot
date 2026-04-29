# Task phaseF.options-gex-panel: GEX 前端仪表盘（workbench）

**Phase**: Phase F.1  
**Status**: pending  
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/frontends/workbench/src/components/GEXPanel.tsx`，集成到 `RiskReviewCenter.tsx`（最顶部）。

### UI 结构

```
[ Ticker 选择 SPY / QQQ / IWM ] [ DTE <= 45 ] [ Refresh ]

─── 关键水位 ──────────────────────────────────────────────
[ Gamma Flip: $xxx ] [ Major Magnet: $xxx ] [ Net GEX: $xxB ]
[ High Vol Trigger: $xxx ]

─── 各行权价 GEX 分布 ─────────────────────────────────────
BarChart（横轴=strike，纵轴=net_gex，正值绿/负值红）
竖虚线标注当前价格

─── 解读提示 ─────────────────────────────────────────────
正 GEX → 做市商 long gamma → 波动率被压制，区间整理
负 GEX → 做市商 short gamma → 波动放大，趋势加速
```

使用 Recharts `BarChart`（已在 workbench 依赖中）。

---

## 验收标准

- [ ] **AC-1**: 文件存在
  - `test -f apps/stock-assistant/frontends/workbench/src/components/GEXPanel.tsx`
- [ ] **AC-2**: Recharts 组件使用
  - `grep -q "BarChart\|recharts" apps/stock-assistant/frontends/workbench/src/components/GEXPanel.tsx`
- [ ] **AC-3**: 集成进 RiskReviewCenter
  - `grep -q "GEXPanel" apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
- [ ] **AC-4**: dark-theme tokens
  - `grep -q "#0E1014\|#151619\|#00C087" apps/stock-assistant/frontends/workbench/src/components/GEXPanel.tsx`
- [ ] **AC-5**: type-check + build 通过
  - `(cd apps/stock-assistant/frontends/workbench && npm run type-check)` 退出码 0
  - `(cd apps/stock-assistant/frontends/workbench && npm run build)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/frontends/workbench/src/components/GEXPanel.tsx`

修改：
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`（新增 GEX 类型定义和 fetch 函数）
