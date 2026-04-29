# Task phaseF5.quant-signals-panel: QuantSignalsPanel 前端面板

**Phase**: Phase F.5
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/frontends/workbench/src/components/QuantSignalsPanel.tsx`，添加到 `RiskReviewCenter.tsx`。

### UI 设计

- 统一标题栏 + Ticker 输入 + 查询按钮
- **Beneish M-Score 区块**
  - M-Score 数值 + 风险等级徽章（safe=绿/grey=黄/manipulator=红）
  - 8 个比率明细（DSRI、GMI、AQI、SGI、DEPI、SGAI、LVGI、TATA）小卡片
  - 解读文本
- **Russell 调仓预览区块**
  - 当前指数归属、市值、估算排名
  - proximity_score 进度条（越高越接近边界）
  - rebalance_signal 徽章（颜色区分方向）
- 空态 / 加载中 / 错误态
- 沿用 dark-theme 设计语言：`#0E1014` / `#151619` / `#00C087`

---

## 验收标准

- [ ] **AC-1**: 文件存在
  - `test -f apps/stock-assistant/frontends/workbench/src/components/QuantSignalsPanel.tsx`

- [ ] **AC-2**: 注册到 RiskReviewCenter
  - `grep -q "QuantSignalsPanel" apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`

- [ ] **AC-3**: 关键符号存在
  - `grep -q "BeneishSection\|RussellSection\|QuantSignalsPanel" apps/stock-assistant/frontends/workbench/src/components/QuantSignalsPanel.tsx`

- [ ] **AC-4**: API 客户端函数存在
  - `grep -q "fetchQuantSignalsSummary\|QuantSignalsSummary" apps/stock-assistant/frontends/workbench/src/api/client.ts`

- [ ] **AC-5**: TypeScript 编译通过
  - `(cd apps/stock-assistant/frontends/workbench && npm run build)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/frontends/workbench/src/components/QuantSignalsPanel.tsx`

修改：
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`

> **批次开发说明**：F.5.1–F.5.3 在同一工作树批量开发并统一提交。
