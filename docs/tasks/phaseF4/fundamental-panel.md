# Task phaseF4.fundamental-panel: 基本面信号前端面板

**Phase**: Phase F.4
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/frontends/workbench/src/components/FundamentalPanel.tsx`，集成到 `RiskReviewCenter.tsx`。

### UI 结构

```
─── 基本面信号（PEAD + Piotroski）──────────────────────────
[ Ticker 输入 ] [ 查询 ]

─── PEAD（盈利公告后漂移）──────────────────────────────────
最新季度：Q3 2024  实际 EPS: $1.85  预期: $1.77  超预期 +4.5%
信号强度：████████░░ 0.78  [大幅超预期]

历史漂移（同类 surprise）：
  7 日：+1.2%   30 日：+3.8%   60 日：+6.2%

─── Piotroski F-Score ──────────────────────────────────────
评分：7 / 9  [优质]  ████████░░

明细：
✓ ROA > 0         ✓ 经营现金流 > 0   ✓ ROA 改善
✓ 现金质量好       ✗ 杠杆率降低       ✓ 流动性改善
✓ 无稀释增发       ✓ 毛利率改善       ✗ 资产周转率下降
```

---

## 验收标准

- [ ] **AC-1**: 文件存在
  - `test -f apps/stock-assistant/frontends/workbench/src/components/FundamentalPanel.tsx`

- [ ] **AC-2**: API 调用
  - `grep -q "fundamental/summary\|fetchFundamental" apps/stock-assistant/frontends/workbench/src/components/FundamentalPanel.tsx`

- [ ] **AC-3**: 集成进 RiskReviewCenter
  - `grep -q "FundamentalPanel" apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`

- [ ] **AC-4**: dark-theme tokens
  - `grep -q "#0E1014\|#151619\|#00C087" apps/stock-assistant/frontends/workbench/src/components/FundamentalPanel.tsx`

- [ ] **AC-5**: Piotroski 评分展示
  - `grep -q "piotroski\|F-Score\|fscore" apps/stock-assistant/frontends/workbench/src/components/FundamentalPanel.tsx`

- [ ] **AC-6**: type-check + build 通过
  - `(cd apps/stock-assistant/frontends/workbench && env -u GVM_ROOT npm run type-check)` 退出码 0
  - `(cd apps/stock-assistant/frontends/workbench && env -u GVM_ROOT npm run build)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/frontends/workbench/src/components/FundamentalPanel.tsx`

修改：
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`

> **批次开发说明**：F.4.1–F.4.3 在同一工作树批量开发并统一提交。
