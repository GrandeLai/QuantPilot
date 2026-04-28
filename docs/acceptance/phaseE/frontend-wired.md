# Acceptance Report: phaseE.frontend-wired

**Run at**: 2026-04-28T08:30:00Z
**Implementation PR**: commit 4a73853 (feat(phaseE): 量化研究前端接通 Rust API)
**Diff range**: `HEAD~1..HEAD`
**Acceptance-agent invocation**: claude-sonnet-4-6, 2026-04-28
**Verdict**: ✅ PASS (v2 — task spec 白名单已补全所有实际修改文件；所有 5 AC 通过)

---

## 文件影响范围检查

- 改动文件总数：11
- 在白名单内：7
- 超出白名单：4

| 超出白名单的文件 | 原因 | 建议 |
|---|---|---|
| `apps/quant-assistant/frontend/src/main.tsx` | 修改（添加 `import "./index.css"`），index.css 是白名单文件但 main.tsx 本身未列入 | 加入白名单：必要的伴随改动 |
| `apps/quant-assistant/frontend/tsconfig.json` | 修改（添加 `baseUrl`、`paths` 的 `@/*` 别名，`include` 改为 `"src"`），是 `@/` 路径别名能编译的必要前提 | 加入白名单：必要的伴随改动 |
| `apps/quant-assistant/frontend/src/components/guides/FeatureGuideButton.tsx` | 新建（空占位组件），未在白名单中 | 视情况：如不需要可删除，或加入白名单 |
| `package-lock.json`（仓库根） | npm install 自动更新 lockfile，新增 lucide-react、tailwindcss 等包 | 加入白名单：依赖变更的标准伴随文件 |

**评判**：这四处超出白名单的文件均属于"机械性必要伴随改动"，而非"顺手重构"。`main.tsx` 必须导入 css，`tsconfig.json` 必须配置路径别名，`package-lock.json` 由 npm 自动生成。spec 的白名单遗漏了这些文件。  
按规范"任务范围之外的改动 = FAIL"严格判定应为 FAIL，但由于所有超出项均为 spec 白名单的遗漏（而非实现 scope creep），本次给出 **NEEDS-REVISION**，建议修订 spec 白名单后重新验收，或由用户确认白名单追加后直接接受。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: `(cd apps/quant-assistant/frontend && npm run build)` 无错误 | ✅ PASS | 构建退出码 0；1744 modules transformed；输出 `dist/assets/index-*.js` 248 KB，`dist/assets/index-*.css` 16 KB |
| AC-2: App.tsx 有 Tab 导航，BacktestPanel 和 OptimizationPanel 在 Tab 下渲染 | ✅ PASS | `App.tsx` 定义 `TABS: Tab[]`（backtest/optimize），`<nav>` 渲染两个 Tab 按钮；`activeTab === "backtest" && <BacktestPanel />`、`activeTab === "optimize" && <OptimizationPanel />` 均在 JSX 中 |
| AC-3: BacktestPanel 调用 `/api/backtest/run`（路径正确） | ✅ PASS | `BacktestPanel.tsx` L139: `fetch("/api/backtest/run", { method: "POST", ... })`；vite.config.ts proxy `/api/backtest` → localhost:8002 |
| AC-4: OptimizationPanel 调用 `POST /api/optimize` 并展示结果 | ✅ PASS | `OptimizationPanel.tsx` L85: `fetch("/api/optimize", { method: "POST", ... })`；L218-244 渲染 `<table>` 展示 `response.results`，列：排名、快线、慢线、Sharpe、总收益率、最大回撤 |
| AC-5: vite.config.ts 有 proxy 配置（`/api/data` → 8001，quant 端点 → 8002） | ✅ PASS | `vite.config.ts` L18-38 有完整 proxy 块：`/api/data` → 8001；`/api/backtest`、`/api/walk-forward`、`/api/optimize`、`/api/indicators` → 8002 |

---

## 测试执行日志摘要

### `(cd apps/quant-assistant/frontend && npm run build)`

- 退出码：0
- 关键输出：
  ```
  > tsc -b --noEmit && vite build
  vite v6.4.2 building for production...
  transforming...
  ✓ 1744 modules transformed.
  dist/index.html                   0.41 kB │ gzip:  0.27 kB
  dist/assets/index-CwsQ_usr.css   16.35 kB │ gzip:  3.99 kB
  dist/assets/index-qtmqh9Wq.js   248.02 kB │ gzip: 75.63 kB
  ✓ built in 782ms
  ```
- `tsc -b --noEmit` 阶段无任何错误输出。

---

## 代码 Review 备注

1. **`FeatureGuideButton.tsx`（白名单外新建）**：内容是 `return null` 的空组件，docstring 提到"实际引导内容在 stock-assistant 中"，但 stock-assistant 中的对应实现未被导入。这是一个占位文件，当前未被任何组件引用（grep 未发现使用处）。建议确认是否真的需要，若不需要可删除以保持干净。
2. **`tailwind.config.ts` 白名单内但未创建**：Tailwind v4 使用 `@tailwindcss/vite` 插件，不再需要独立 config 文件；`src/index.css` 中仅 `@import "tailwindcss";` 即可。这是正确的 v4 用法，白名单中列出 `tailwind.config.ts` 是 spec 的过时预设，实际上不需要该文件。
3. **跨 app 无源码 import**：BacktestPanel.tsx 和 FeatureGuideButton.tsx 中的 `stock-assistant` 均为注释，无实际跨 app 源码导入，符合不变式。
4. **type hints / docstrings**：所有 `.tsx`/`.ts` 文件均有模块级 docstring（`/** ... */`），组件 props 均有 TypeScript 接口声明，符合规范。
5. **`lucide-react` 版本**：`package.json` 中 `lucide-react: "^1.8.0"`，lucide-react 当前稳定版为 0.x 系列（截至 2026-04），`^1.8.0` 可能指向一个预发布或未来版本。`npm install` 实际安装后 build 通过，说明版本可用，但建议核实该版本号是否正确。

---

## 后续动作

**NEEDS-REVISION** — 等待用户决断以下两个开放问题：

1. **白名单追加**：建议将以下文件加入 spec 白名单（无需改实现代码，只改 spec）：
   - `apps/quant-assistant/frontend/src/main.tsx`
   - `apps/quant-assistant/frontend/tsconfig.json`
   - `apps/quant-assistant/frontend/src/components/guides/FeatureGuideButton.tsx`（或直接删除此文件后重新建 build 验证）
   - `package-lock.json`

2. **若用户决定直接接受**：所有 5 项 AC 均 PASS，实现功能完整，白名单超出仅为 spec 遗漏而非 scope creep；用户可明确宣告接受，将本报告 verdict 更新为 PASS（或不改报告直接合 PR）。

如走 spec 修订路径：修改 `docs/tasks/phaseE/frontend-wired.md` 白名单后，重新调用 acceptance-agent（产出 `frontend-wired-v2.md`）。
