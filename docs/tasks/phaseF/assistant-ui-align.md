# Task phaseF.assistant-ui-align: 对齐 assistant 前端 UI 到 workbench 设计语言

**Phase**: Phase F.1 修复
**Status**: pending
**Implementation PR**: <pending>
**Created**: 2026-04-29
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

5174 端口 assistant frontend 视觉上"很奇怪"——白色背景 + 默认浏览器按钮 + 朴素文字 + 还有 `Error: Request failed: 404` 直接显示给用户。

根因（用户也观察到了）：
1. **Tailwind 没装**：5 个 view 组件代码已写满 `grid gap-4 md:grid-cols-2 rounded-lg border-[#d1d5db]` 之类的 Tailwind 类，但 `package.json` 既没 `tailwindcss` 也没 `@tailwindcss/vite`，class 全部成了死代码。
2. **App.tsx 退而求其次用 inline style**：因为没 Tailwind 可用，作者只能给容器加内联 style；按钮也是默认浏览器外观。
3. **缺 index.css**：`main.tsx` 不 import 任何 CSS。
4. **后端 advisor 路由不存在**：`grep -rn "advisor" apps/stock-assistant/backend/` 无输出。前端调 `/api/advisor/*` 全部 404，UI 把原始错误信息直接打印出来。

本任务：把 Tailwind 接上、5 个 view 组件按 workbench 风格重写、404 走优雅空状态而不是抛错给用户。

**注**：advisor 后端路由是另一个独立的事（要么实现要么取消该 feature），不在本任务范围。本任务只解决"UI 显示"问题；advisor 数据接入留作后续 task `assistant-advisor-backend`。

### 做什么

#### 1. 接入 Tailwind v4（与 workbench 一致）

`apps/stock-assistant/frontends/assistant/package.json`：
- 加 `dependencies`: `clsx@^2.1.1`、`tailwind-merge@^3.5.0`
- 加 `devDependencies`: `tailwindcss@^4.2.2`、`@tailwindcss/vite@^4.2.2`
- 注：lucide-react 已在 deps，复用

`apps/stock-assistant/frontends/assistant/vite.config.ts`：
- 在 plugins 数组追加 `tailwindcss()` 插件

`apps/stock-assistant/frontends/assistant/src/index.css`（新建）：
- `@import "tailwindcss";`
- 设置 body bg `#0E1014`、color `#FFFFFF`、字体栈
- 提供与 workbench 一致的设计 token（不必照搬 oklch 调色板，只要常用 hex 即可）

`apps/stock-assistant/frontends/assistant/src/main.tsx`：
- 顶部加 `import "./index.css";`

`apps/stock-assistant/frontends/assistant/src/lib/utils.ts`（新建）：
- 标准 `cn()` 工具：`twMerge(clsx(inputs))`

#### 2. 重写 `App.tsx` 为 dark-theme shell

- bg `#0E1014`、min-h-screen
- 顶栏：标题 + lucide `Sparkles`/`LineChart` icon
- Tab 栏：与 workbench 风格一致（active = `#00C087` 背景黑字、其它 = `#151619` 边框灰字 hover 高亮）
- 内容区：rounded-xl border + bg `#0E1014` 内嵌 `#151619` 卡片

#### 3. 重写 5 个 view 组件为统一 KPI 卡片风格

每个组件统一形态：
```
<section>
  <Header (icon + title + subtitle)>
  if loading → <LoadingSkeleton/>
  else if error → <EmptyState reason="..." />
  else → <KPI grid> + <DetailList>
```

- `PortfolioOverview`：4 KPI（净资产、现金占比、持仓数、姿态）+ 持仓表
- `OpportunityPool`：opportunities 卡片列表（subject、recommendation、confidence、freshness）
- `RebalanceSuggestions`：placeholder + 后端未对接说明（advisor 后端未实现）
- `RiskRadar`：risks 卡片列表（同 OpportunityPool）
- `ReviewAsk`：4 KPI 摘要（净资产、现金占比、机会数、风险数）+ 文字总结

#### 4. 优雅处理 404

当 fetch 报错（含 404）时，**不要**直接 `setError(String(err))`。改为分类：
- 404 / "Request failed: 404" → 空状态卡片：`数据暂未接入（advisor 后端尚未实现）`
- 其它错误 → 红色错误条 with retry button

新建 `src/components/ui/EmptyState.tsx`（or inline helper），包含 "暂未接入"、"加载中"、"暂无数据" 三种状态。

#### 5. 不动的部分

- `navigation.ts` / `navigation.test.ts`：保持现有 5 个 tab + 测试不动
- `store/advisorStore.ts`：保持
- `api/client.ts`：保持 URL（前端调用契约不变；后端实现是另一个 task）
- `api/client.test.ts`：保持
- 后端：完全不动

### 不做什么

- 不实现 advisor 后端路由（独立任务）
- 不引入 shadcn/radix 全套（只装 tailwind + clsx + tailwind-merge，最小集）
- 不改 navigation / 数据结构 / API URL
- 不动 workbench

---

## 验收标准

- [ ] **AC-1**: deps 已加 — 4 项
  - `grep -q "tailwindcss" apps/stock-assistant/frontends/assistant/package.json`
  - `grep -q "@tailwindcss/vite" apps/stock-assistant/frontends/assistant/package.json`
  - `grep -q "\"clsx\"" apps/stock-assistant/frontends/assistant/package.json`
  - `grep -q "tailwind-merge" apps/stock-assistant/frontends/assistant/package.json`
- [ ] **AC-2**: Tailwind 已接入 vite + main 已 import index.css
  - `grep -q "tailwindcss" apps/stock-assistant/frontends/assistant/vite.config.ts`
  - `test -f apps/stock-assistant/frontends/assistant/src/index.css`
  - `grep -q "import \"./index.css\"" apps/stock-assistant/frontends/assistant/src/main.tsx`
  - `grep -q "@import \"tailwindcss\"" apps/stock-assistant/frontends/assistant/src/index.css`
- [ ] **AC-3**: 工具 + UI helpers
  - `test -f apps/stock-assistant/frontends/assistant/src/lib/utils.ts`
  - `grep -q "twMerge\|tailwind-merge" apps/stock-assistant/frontends/assistant/src/lib/utils.ts`
- [ ] **AC-4**: 404 优雅处理 — 在所有 5 个 view 组件中至少有 1 处 "暂未接入" 文案
  - `grep -lc "暂未接入\|未实现\|advisor 后端" apps/stock-assistant/frontends/assistant/src/components/*.tsx | grep -v ":0$" | wc -l` ≥ 1
- [ ] **AC-5**: type-check + build 通过
  - `(cd apps/stock-assistant/frontends/assistant && npm run type-check)` 退出码 0
  - `(cd apps/stock-assistant/frontends/assistant && npm run build)` 退出码 0
- [ ] **AC-6**: navigation 测试无回归
  - `(cd apps/stock-assistant/frontends/assistant && node --test --experimental-strip-types src/navigation.test.ts src/api/client.test.ts)` 退出码 0
- [ ] **AC-7**: 不动 workbench / 后端
  - `git diff main --name-only -- apps/stock-assistant/frontends/workbench/ apps/stock-assistant/backend/ apps/quant-assistant/ common/` 输出为空
- [ ] **AC-8**: dark-theme tokens 出现在重写后的组件
  - `grep -l "#0E1014\|#151619\|#2A2D35\|#00C087" apps/stock-assistant/frontends/assistant/src/App.tsx apps/stock-assistant/frontends/assistant/src/components/*.tsx | wc -l` ≥ 4

---

## 测试集合

```bash
(cd apps/stock-assistant/frontends/assistant && npm install --no-audit --no-fund) # 一次性
(cd apps/stock-assistant/frontends/assistant && npm run type-check)
(cd apps/stock-assistant/frontends/assistant && npm run build)
(cd apps/stock-assistant/frontends/assistant && node --test --experimental-strip-types src/navigation.test.ts src/api/client.test.ts)
git diff main --name-only -- apps/stock-assistant/frontends/workbench/ apps/stock-assistant/backend/
```

---

## 文件影响范围

新建：
- `apps/stock-assistant/frontends/assistant/src/index.css`
- `apps/stock-assistant/frontends/assistant/src/lib/utils.ts`
- `docs/tasks/phaseF/assistant-ui-align.md`

修改：
- `apps/stock-assistant/frontends/assistant/package.json`（加 deps）
- `apps/stock-assistant/frontends/assistant/package-lock.json`（npm install 自动更新）
- `apps/stock-assistant/frontends/assistant/vite.config.ts`（加 tailwind 插件）
- `apps/stock-assistant/frontends/assistant/src/main.tsx`（import css）
- `apps/stock-assistant/frontends/assistant/src/App.tsx`（重写 shell）
- `apps/stock-assistant/frontends/assistant/src/components/PortfolioOverview.tsx`
- `apps/stock-assistant/frontends/assistant/src/components/OpportunityPool.tsx`
- `apps/stock-assistant/frontends/assistant/src/components/RebalanceSuggestions.tsx`
- `apps/stock-assistant/frontends/assistant/src/components/RiskRadar.tsx`
- `apps/stock-assistant/frontends/assistant/src/components/ReviewAsk.tsx`

monorepo 根 `package-lock.json` 也可能因 npm install 而更新（npm workspace 自动），列入白名单避免误报。

不允许改：所有其它路径。

---

## 引用

- **设计来源**：用户视觉反馈（"UI 那么奇怪，请对齐原来的 UI"）；workbench 设计语言为对齐目标
- **类比模式**：`apps/stock-assistant/frontends/workbench/` 同款 Tailwind v4 + dark theme
- **遗留**：advisor 后端 404 是单独任务（标记为 TODO）
