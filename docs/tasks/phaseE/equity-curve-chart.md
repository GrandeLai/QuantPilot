# Task phaseE.equity-curve-chart: BacktestPanel 权益曲线图

**Phase**: Phase E
**Status**: pending
**Created**: 2026-04-28
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

BacktestPanel 的回测结果中已有 `equity_curve: number[]`（每根 K 线结束时的组合净值），但当前只展示文字指标，没有可视化图表。本任务在结果区顶部添加权益曲线折线图。

### 做什么

1. **新建 `src/components/EquityCurveChart.tsx`**：纯 SVG 折线图组件
   - Props: `{ data: number[]; initialCash: number; className?: string }`
   - 响应式 viewBox（宽度撑满，固定高度 160px）
   - 折线颜色：盈利为绿色（`#22c55e`），亏损为红色（`#ef4444`）
   - 虚线水平基准线（initial_cash 水位）
   - Y 轴左侧 3 个刻度标签（最小值、初始、最大值）格式化为 `$xM` / `$xK`
   - 鼠标悬停时显示当前点净值 tooltip（SVG foreignObject 或绝对定位 div）
   - 数据点 < 2 时渲染空状态占位

2. **在 BacktestPanel 结果区添加图表**：
   - 位置：标题行（MA(fast,slow) · symbol）下方，核心指标 grid 上方
   - 包裹在带 border 的卡片容器中

### 不做什么

- 不添加新的 npm 依赖（纯 SVG + React hooks）
- 不修改 Rust 后端
- 不修改 OptimizationPanel
- 不添加 K 线叠加图（留后续）

---

## 验收标准

- [ ] **AC-1**: `test -f apps/quant-assistant/frontend/src/components/EquityCurveChart.tsx`
- [ ] **AC-2**: `grep -c "viewBox\|polyline\|<svg" apps/quant-assistant/frontend/src/components/EquityCurveChart.tsx` >= 2（使用 SVG 实现）
- [ ] **AC-3**: `grep -c "EquityCurveChart" apps/quant-assistant/frontend/src/components/BacktestPanel.tsx` >= 2（import + 使用）
- [ ] **AC-4**: `(cd apps/quant-assistant/frontend && npm run build)` 无错误

---

## 文件影响范围（白名单）

新建：
- `apps/quant-assistant/frontend/src/components/EquityCurveChart.tsx`

修改：
- `apps/quant-assistant/frontend/src/components/BacktestPanel.tsx`
