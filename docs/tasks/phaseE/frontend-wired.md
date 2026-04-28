# Task phaseE.frontend-wired: 量化研究前端接通 Rust API

**Phase**: Phase E
**Status**: pending
**Created**: 2026-04-28
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

phaseD.api-expand 完成后，Rust quant-assistant 后端暴露了完整的 HTTP API。本任务将 `apps/quant-assistant/frontend/` 从 Phase A skeleton 变为可实际运行的研究前端。

### 做什么

1. **更新 `vite.config.ts`**：
   - `/api/data/*` → stock-assistant（8001）
   - `/api/backtest/*`, `/api/walk-forward`, `/api/optimize`, `/api/indicators` → quant-assistant（8002）
2. **添加前端依赖**：`lucide-react`、`tailwindcss`、`@tailwindcss/vite`（与 stock-assistant 保持一致）
3. **更新 `App.tsx`**：
   - 添加 Tab 导航（回测 / 优化 / 指标）
   - 接入 BacktestPanel（现有组件已 copy）
4. **适配 BacktestPanel**：
   - 调整 fetch 路径 → `/api/backtest/run`（Rust 端点）
   - 适配响应字段（Rust 返回 `metrics.total_return` 等）
5. **新增 OptimizationPanel**：调用 `POST /api/optimize`，展示 top-N 参数表格
6. **`npm run build` 成功**

### 不做什么

- 不做 SignalsPanel / MLStrategyPanel / ValidationLab（留后续）
- 不改 stock-assistant 前端
- 不改 Rust 后端

---

## 验收标准

- [ ] **AC-1**: `(cd apps/quant-assistant/frontend && npm run build)` 无错误
- [ ] **AC-2**: App.tsx 有 Tab 导航，BacktestPanel 和 OptimizationPanel 在 Tab 下渲染
- [ ] **AC-3**: BacktestPanel 调用 `/api/backtest/run` 而不是 `/api/backtest/run`（路径正确）
- [ ] **AC-4**: OptimizationPanel 调用 `POST /api/optimize` 并展示结果
- [ ] **AC-5**: vite.config.ts 有 proxy 配置（`/api/data` → 8001，quant 端点 → 8002）

---

## 文件影响范围（白名单）

```
修改：
- apps/quant-assistant/frontend/package.json
- apps/quant-assistant/frontend/vite.config.ts
- apps/quant-assistant/frontend/src/App.tsx
- apps/quant-assistant/frontend/src/components/BacktestPanel.tsx

新建：
- apps/quant-assistant/frontend/src/components/OptimizationPanel.tsx
- apps/quant-assistant/frontend/src/lib/utils.ts（cn 函数）
- apps/quant-assistant/frontend/tailwind.config.ts
- apps/quant-assistant/frontend/src/index.css
```
