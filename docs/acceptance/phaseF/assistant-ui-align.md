# Acceptance Report: phaseF.assistant-ui-align

**Run at**: 2026-04-28T00:00:00Z
**Implementation PR**: commit ef491c7
**Diff range**: `ef491c7^..ef491c7`
**Acceptance-agent invocation**: claude-sonnet-4-6 / phaseF.assistant-ui-align
**Verdict**: NEEDS-REVISION

---

## 文件影响范围检查

- 改动文件总数：14
- 在白名单内：14
- 超出白名单：0

Changed files vs. whitelist:

| 文件 | 白名单状态 |
|---|---|
| `apps/stock-assistant/frontends/assistant/package.json` | OK (修改白名单) |
| `apps/stock-assistant/frontends/assistant/src/App.tsx` | OK (修改白名单) |
| `apps/stock-assistant/frontends/assistant/src/components/OpportunityPool.tsx` | OK (修改白名单) |
| `apps/stock-assistant/frontends/assistant/src/components/PortfolioOverview.tsx` | OK (修改白名单) |
| `apps/stock-assistant/frontends/assistant/src/components/RebalanceSuggestions.tsx` | OK (修改白名单) |
| `apps/stock-assistant/frontends/assistant/src/components/ReviewAsk.tsx` | OK (修改白名单) |
| `apps/stock-assistant/frontends/assistant/src/components/RiskRadar.tsx` | OK (修改白名单) |
| `apps/stock-assistant/frontends/assistant/src/components/ui/StateMessages.tsx` | OK (新建；spec 说 EmptyState.tsx "or inline helper"；调用方 prompt 明确将 StateMessages.tsx 列入白名单) |
| `apps/stock-assistant/frontends/assistant/src/index.css` | OK (新建白名单) |
| `apps/stock-assistant/frontends/assistant/src/lib/utils.ts` | OK (新建白名单) |
| `apps/stock-assistant/frontends/assistant/src/main.tsx` | OK (修改白名单) |
| `apps/stock-assistant/frontends/assistant/vite.config.ts` | OK (修改白名单) |
| `docs/tasks/phaseF/assistant-ui-align.md` | OK (新建白名单) |
| `package-lock.json` (monorepo root) | OK (spec 明确列入白名单) |

注：spec 列出的 `apps/stock-assistant/frontends/assistant/package-lock.json` 实际未在此 commit 中改动（npm workspace 只更新了 monorepo root lock）。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: deps 已加 — tailwindcss, @tailwindcss/vite, clsx, tailwind-merge | ✅ PASS | 全部 4 项 grep 通过；package.json 中 clsx@^2.1.1 在 dependencies，tailwind-merge@^3.5.0 在 dependencies，tailwindcss@^4.2.2 和 @tailwindcss/vite@^4.2.2 在 devDependencies |
| AC-2: Tailwind 已接入 vite + main 已 import index.css | ✅ PASS | vite.config.ts 有 `import tailwindcss from "@tailwindcss/vite"` 并在 plugins 数组中调用；index.css 存在且首行为 `@import "tailwindcss"`；main.tsx 第 4 行 `import "./index.css"` |
| AC-3: 工具 + UI helpers (utils.ts with twMerge) | ✅ PASS | `src/lib/utils.ts` 存在，内含 `twMerge(clsx(inputs))` 形式的 `cn()` 工具函数 |
| AC-4: 404 优雅处理 — 至少 1 个 components/*.tsx 含 "暂未接入\|未实现\|advisor 后端" | ⚠️ PARTIAL | **spec 的精确 grep 命令**（glob `components/*.tsx`）返回 0，因为文案在 `components/ui/StateMessages.tsx` 而非直接在顶层组件。但 `StateMessages.tsx` 中 `ErrorOrEmptyState` 含 "未实现该路由" 和 "advisor 后端尚未实现该路由" 文案，被全部 5 个 view 组件通过 `<ErrorOrEmptyState error={error} />` 调用，功能意图完全满足。这是 spec glob 粒度 vs. 实现结构的差异：实现把共享 UI helper 提取到 `ui/` 子目录，这是更好的工程做法，但 spec 的 grep 没有涵盖子目录。建议修订 AC-4 的 grep 路径为 `src/components/**/*.tsx` 或将 `StateMessages.tsx` 加入显式检查路径。|
| AC-5: type-check + build 通过 | ✅ PASS | `npm run type-check` 退出码 0 (tsc --noEmit 无错误)；`npm run build` 退出码 0 (vite build 成功：244 kB JS + 14 kB CSS，146ms) |
| AC-6: navigation 测试无回归 | ✅ PASS | `node --test --experimental-strip-types src/navigation.test.ts src/api/client.test.ts` 退出码 0；6 tests, 0 fail |
| AC-7: 不动 workbench / 后端 | ✅ PASS | `git diff main --name-only -- apps/stock-assistant/frontends/workbench/ apps/stock-assistant/backend/ apps/quant-assistant/ common/` 输出为空 |
| AC-8: dark-theme tokens 在重写后的组件 | ✅ PASS | 6 个文件含 `#0E1014\|#151619\|#2A2D35\|#00C087` (>= 4 要求)：App.tsx、PortfolioOverview.tsx、OpportunityPool.tsx、RebalanceSuggestions.tsx、RiskRadar.tsx、ReviewAsk.tsx |

---

## 测试执行日志摘要

### `npm install --no-audit --no-fund`
- 退出码：0
- 输出：`up to date in 460ms`（依赖已满足）

### `npm run type-check`
- 退出码：0
- 输出：tsc 无错误，无警告

### `npm run build`
- 退出码：0
- 关键输出：
  ```
  vite v8.0.10 building client environment for production...
  ✓ 1744 modules transformed.
  dist/assets/index-D_SUAoRU.css   14.47 kB │ gzip: 3.75 kB
  dist/assets/index-xZ48Kvj7.js   244.18 kB │ gzip: 76.01 kB
  ✓ built in 146ms
  ```

### `node --test --experimental-strip-types src/navigation.test.ts src/api/client.test.ts`
- 退出码：0
- 输出：6 tests, 0 fail, 0 cancelled, 0 skipped

### `git diff main --name-only -- workbench/ backend/`
- 退出码：0
- 输出：（空）— workbench 和后端完全未动

---

## 代码 Review 备注

1. **StateMessages.tsx 设计**：实现选择将 `LoadingState`、`ErrorOrEmptyState`、`EmptyState`、`KPICard` 等 UI helpers 聚合在 `src/components/ui/StateMessages.tsx`，而非 spec 建议的单文件 `EmptyState.tsx`。这是更好的封装，不违反任何不变式。

2. **404 检测逻辑**：`ErrorOrEmptyState` 中用正则 `/404|Request failed: 4|not found/i` 检测是否为未实现 404，降级为友好空状态。逻辑合理，覆盖了 spec 场景（"Request failed: 404"）。

3. **RebalanceSuggestions**：spec 要求 "placeholder + 后端未对接说明"，实现做了更完整的版本（也从后端拉 opportunities + risks 来生成建议列表，404 时走 `ErrorOrEmptyState` 友好降级）。超出 spec 但方向正确，无副作用。

4. **跨 app import**：无违规；所有 import 限于 `assistant` app 内部和 `@quantpilot/common-frontend`。

5. **无 shadcn/radix 引入**：符合 spec "最小集"约束；仅 tailwind + clsx + tailwind-merge。

---

## 后续动作

AC-4 状态为 PARTIAL，原因是 spec 的 grep 路径（`components/*.tsx`）不匹配实现的子目录结构（`components/ui/StateMessages.tsx`）。有两个选择：

**选项 A（推荐）**：修订 AC-4 的 grep 命令，将路径改为 `src/components/**/*.tsx` 或显式加入 `src/components/ui/StateMessages.tsx`，并重新验收 → verdict 变 PASS。

**选项 B**：要求 implementation agent 将 "暂未接入" 等文案也直接写入某个顶层 `components/*.tsx`（例如 RebalanceSuggestions.tsx 中加一行注释文本）以满足原 grep。

建议采用选项 A，因为实现的结构更合理，spec 的 grep 是机械性的工具约束而非功能需求的本质。
