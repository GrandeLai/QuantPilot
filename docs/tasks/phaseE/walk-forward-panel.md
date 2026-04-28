# Task phaseE.walk-forward-panel: Walk-Forward 验证面板

**Phase**: Phase E (post)
**Status**: pending
**Created**: 2026-04-28
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

quant-assistant 前端目前有两个 Tab：回测（BacktestPanel）和参数优化（OptimizationPanel）。后端 `POST /api/walk-forward` 端点已实现但前端没有 UI 入口。本任务新增 Walk-Forward 验证面板并接入该端点。

### 做什么

1. **新建 `src/components/WalkForwardPanel.tsx`**：Walk-Forward 验证面板

   **输入表单**：
   - Symbol（文本输入，同 BacktestPanel 格式）
   - Timeframe 下拉（1d / 1w / 1h / 4h）
   - Fast MA period（数字输入）
   - Slow MA period（数字输入）
   - Initial Cash（数字输入）
   - Train Size（训练窗口 bar 数，数字输入）
   - Test Size（测试窗口 bar 数，数字输入）

   **调用流程**（同 BacktestPanel）：
   1. `GET /api/data/klines?symbol=...&timeframe=...&limit=500` 从 stock-assistant（8001）拉 K 线
   2. 提取 `close` 数组
   3. `POST /api/walk-forward` 发送请求

   **请求体格式**（POST /api/walk-forward）：
   ```json
   {
     "closes": [float],
     "fast_period": int,
     "slow_period": int,
     "initial_cash": float,
     "train_size": int,
     "test_size": int
   }
   ```

   **结果展示**：
   - 使用 `EquityCurveChart` 组件展示拼接后的 `equity_curve`
   - Window 汇总表格：每行显示窗口编号、训练区间（bar 范围）、测试区间（bar 范围）
   - 汇总行：n_windows 总数

2. **在 `App.tsx` 增加第三个 Tab**：
   - Tab id: `"walk-forward"`
   - 图标：使用 lucide-react 的 `GitBranch` 图标
   - 标签文字：`"Walk-Forward"`
   - 渲染：`{activeTab === "walk-forward" && <WalkForwardPanel />}`

### 不做什么

- 不修改 Rust 后端
- 不修改 BacktestPanel 或 OptimizationPanel 核心逻辑
- 不添加新的 npm 依赖

---

## 验收标准

- [ ] **AC-1**: `test -f apps/quant-assistant/frontend/src/components/WalkForwardPanel.tsx`
- [ ] **AC-2**: `grep -c "walk-forward\|WalkForward\|walk_forward" apps/quant-assistant/frontend/src/components/WalkForwardPanel.tsx` >= 2
- [ ] **AC-3**: `grep -c "WalkForwardPanel\|walk-forward" apps/quant-assistant/frontend/src/App.tsx` >= 2（import + Tab 定义 + 渲染，至少 2 处）
- [ ] **AC-4**: `grep "EquityCurveChart" apps/quant-assistant/frontend/src/components/WalkForwardPanel.tsx` 有输出（复用图表组件）
- [ ] **AC-5**: `(cd apps/quant-assistant/frontend && npm run build)` 无错误

---

## 文件影响范围（白名单）

新建：
- `apps/quant-assistant/frontend/src/components/WalkForwardPanel.tsx`

修改：
- `apps/quant-assistant/frontend/src/App.tsx`
