# Acceptance Report: phaseE.equity-curve-chart

**Run at**: 2026-04-28T00:00:00Z
**Implementation PR**: commits 8d24798 (initial), 7a2f57c (quality fixes)
**Diff range**: `8d24798^..7a2f57c`
**Acceptance-agent invocation**: claude-sonnet-4-6, 2026-04-28
**Verdict**: PASS

---

## 文件影响范围检查

- 改动文件总数：2 (across both commits)
- 在白名单内：2
- 超出白名单：0

Changed files:
- `apps/quant-assistant/frontend/src/components/EquityCurveChart.tsx` — 白名单：新建，MATCH
- `apps/quant-assistant/frontend/src/components/BacktestPanel.tsx` — 白名单：修改，MATCH

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: `test -f apps/quant-assistant/frontend/src/components/EquityCurveChart.tsx` | ✅ PASS | `test -f` 命令退出码 0；文件存在 |
| AC-2: `grep -c "viewBox\|polyline\|<svg" EquityCurveChart.tsx` >= 2 | ✅ PASS | grep -c 输出 4（viewBox×1, polyline×1, <svg×2）|
| AC-3: `grep -c "EquityCurveChart" BacktestPanel.tsx` >= 2 | ✅ PASS | grep -c 输出 2（import 行 + JSX 使用行）|
| AC-4: `npm run build` 无错误 | ✅ PASS | vite build 退出码 0；250 kB bundle 生成，无 TS 错误 |

---

## 测试执行日志摘要

### `test -f apps/quant-assistant/frontend/src/components/EquityCurveChart.tsx`
- 退出码：0
- 关键输出：PASS: file exists

### `grep -c "viewBox\|polyline\|<svg" EquityCurveChart.tsx`
- 退出码：0
- 关键输出：4（>= 2 门槛，通过）

### `grep -c "EquityCurveChart" BacktestPanel.tsx`
- 退出码：0
- 关键输出：2（>= 2 门槛，通过；import + JSX 使用）

### TypeScript 类型检查 (`tsc -b tsconfig.json --noEmit`)
- 退出码：0
- 关键输出：无错误输出

### Vite 生产构建
- 退出码：0
- 关键输出：
  ```
  vite v6.4.2 building for production...
  transforming...
  ✓ 1745 modules transformed.
  rendering chunks...
  computing gzip size...
  dist/index.html                   0.41 kB │ gzip:  0.28 kB
  dist/assets/index-B09R-jeh.css   17.05 kB │ gzip:  4.12 kB
  dist/assets/index-ClE3hMGE.js   250.76 kB │ gzip: 76.59 kB
  ✓ built in 840ms
  ```

---

## 代码 Review 备注

整体质量良好，无阻塞性问题。以下为观察性备注（不影响 verdict）：

1. **SVG 实现符合规范**：纯 SVG + React hooks，无新 npm 依赖，符合 task spec "不做什么" 约束。
2. **质量修复已落地（commit 7a2f57c）**：
   - 移除了死代码 `containerRef`（useRef 未被任何 JSX ref 属性使用）
   - `initialCash !== 0` 的除零保护正确到位（line 122）
   - Y-axis labels 使用 index `i` 作为 key，对于 size-3 稳定数组是合理做法
3. **响应式布局**：`width="100%"` + viewBox="0 0 600 160" 实现宽度自适应；高度 160px 固定符合规范要求
4. **折线颜色逻辑**：对比最终值与 initialCash 决定盈亏色（#22c55e / #ef4444），符合 spec
5. **tooltip 位置自适应**：右侧 30% 区域自动翻转到左侧，避免溢出边界
6. **模块文档注释**：文件顶部有 JSDoc block，符合项目 TypeScript 规范
7. **无跨 app 非法 import**：EquityCurveChart 只 import `react` 和 `@/lib/utils`；BacktestPanel 只 import `@/components/EquityCurveChart`，无 stock-assistant 相关路径
8. **结果区布局位置**：权益曲线位于标题行下方、核心指标 grid 上方，符合 spec 要求

---

## 后续动作

- PR 可合：无阻塞项
- 建议 commit 本报告后合入 main，并更新 `docs/acceptance/INDEX.md`
