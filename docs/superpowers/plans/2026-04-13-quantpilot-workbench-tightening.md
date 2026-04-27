# QuantPilot Workbench Tightening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reshape the existing QuantPilot frontend into a workflow-first quant trading workbench organized around research, strategy, validation, run, and risk/review.

**Architecture:** Keep the existing `frontend/` app and reuse current panels, but insert a new workbench shell and workflow navigation layer that groups topic panels into profit-oriented workflow centers. This avoids a full rewrite and lets the product identity change without breaking current data/API integrations.

**Tech Stack:** React 19, TypeScript, Vite, Zustand, existing QuantPilot frontend components, Node test runner with `--experimental-strip-types`

---

## File Map

- Create `frontend/src/workbench/navigation.ts` — workflow tab definitions
- Create `frontend/src/workbench/navigation.test.ts` — navigation ordering regression test
- Create `frontend/src/workbench/sections.ts` — section-to-panel mapping
- Create `frontend/src/workbench/sections.test.ts` — banned-topic regression test
- Create `frontend/src/components/workbench/WorkbenchShell.tsx` — top-level workflow shell
- Create `frontend/src/components/workbench/ResearchCenter.tsx` — wraps market/screener/crypto research flows
- Create `frontend/src/components/workbench/StrategyLibrary.tsx` — wraps strategy authoring flow
- Create `frontend/src/components/workbench/ValidationCenter.tsx` — wraps validation flow
- Create `frontend/src/components/workbench/RunCenter.tsx` — wraps paper/live run flow
- Create `frontend/src/components/workbench/RiskReviewCenter.tsx` — wraps portfolio/risk review flow
- Modify `frontend/src/App.tsx` — replace topic tabs with workbench shell
- Modify `docs/tab-pages-guide.md` — document new workbench information architecture

### Task 1: Define workflow navigation and lock its order

**Files:**
- Create: `frontend/src/workbench/navigation.ts`
- Test: `frontend/src/workbench/navigation.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
import test from "node:test";
import assert from "node:assert/strict";

import { WORKBENCH_TABS } from "./navigation.ts";

test("workbench tabs follow the profit workflow order", () => {
  assert.deepEqual(
    WORKBENCH_TABS.map((tab) => tab.key),
    ["research", "strategy", "validation", "run", "risk_review"],
  );
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && node --test --experimental-strip-types src/workbench/navigation.test.ts`  
Expected: FAIL with `Cannot find module './navigation.ts'`

- [ ] **Step 3: Write minimal implementation**

`frontend/src/workbench/navigation.ts`

```ts
import { type ComponentType } from "react";
import {
  Activity,
  BookOpen,
  FlaskConical,
  PlayCircle,
  ShieldAlert,
} from "lucide-react";

export type WorkbenchTab =
  | "research"
  | "strategy"
  | "validation"
  | "run"
  | "risk_review";

export interface WorkbenchTabDef {
  key: WorkbenchTab;
  label: string;
  icon: ComponentType<{ size?: number }>;
}

export const WORKBENCH_TABS: WorkbenchTabDef[] = [
  { key: "research", label: "研究中心", icon: Activity },
  { key: "strategy", label: "策略库", icon: BookOpen },
  { key: "validation", label: "验证中心", icon: FlaskConical },
  { key: "run", label: "运行中心", icon: PlayCircle },
  { key: "risk_review", label: "风险与复盘", icon: ShieldAlert },
];
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && node --test --experimental-strip-types src/workbench/navigation.test.ts`  
Expected: PASS with `1 test passed`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/workbench/navigation.ts frontend/src/workbench/navigation.test.ts
git commit -m "feat: define workbench workflow navigation"
```

### Task 2: Build the workbench shell and map workflow sections to existing panels

**Files:**
- Create: `frontend/src/workbench/sections.ts`
- Create: `frontend/src/workbench/sections.test.ts`
- Create: `frontend/src/components/workbench/WorkbenchShell.tsx`
- Create: `frontend/src/components/workbench/ResearchCenter.tsx`
- Create: `frontend/src/components/workbench/StrategyLibrary.tsx`
- Create: `frontend/src/components/workbench/ValidationCenter.tsx`
- Create: `frontend/src/components/workbench/RunCenter.tsx`
- Create: `frontend/src/components/workbench/RiskReviewCenter.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Write the failing test**

```ts
import test from "node:test";
import assert from "node:assert/strict";

import { WORKBENCH_SECTIONS } from "./sections.ts";

test("topic-only tabs are removed from first-class workbench sections", () => {
  assert.deepEqual(Object.keys(WORKBENCH_SECTIONS), [
    "research",
    "strategy",
    "validation",
    "run",
    "risk_review",
  ]);

  assert.equal(WORKBENCH_SECTIONS.research.includes("options"), false);
  assert.equal(WORKBENCH_SECTIONS.research.includes("plugins"), false);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && node --test --experimental-strip-types src/workbench/sections.test.ts`  
Expected: FAIL with `Cannot find module './sections.ts'`

- [ ] **Step 3: Write minimal implementation**

`frontend/src/workbench/sections.ts`

```ts
import type { WorkbenchTab } from "./navigation.ts";

export const WORKBENCH_SECTIONS: Record<WorkbenchTab, string[]> = {
  research: ["market", "screener", "crypto"],
  strategy: ["strategy_workshop"],
  validation: ["validation_lab"],
  run: ["paper_trading", "live_trading"],
  risk_review: ["portfolio", "risk_review"],
};
```

`frontend/src/components/workbench/WorkbenchShell.tsx`

```tsx
import { useState } from "react";

import { WORKBENCH_TABS, type WorkbenchTab } from "@/workbench/navigation";
import ResearchCenter from "./ResearchCenter";
import StrategyLibrary from "./StrategyLibrary";
import ValidationCenter from "./ValidationCenter";
import RunCenter from "./RunCenter";
import RiskReviewCenter from "./RiskReviewCenter";

const VIEW_BY_TAB: Record<WorkbenchTab, JSX.Element> = {
  research: <ResearchCenter />,
  strategy: <StrategyLibrary />,
  validation: <ValidationCenter />,
  run: <RunCenter />,
  risk_review: <RiskReviewCenter />,
};

export default function WorkbenchShell() {
  const [active, setActive] = useState<WorkbenchTab>("research");

  return (
    <div className="space-y-6">
      <nav className="flex gap-2 justify-center">
        {WORKBENCH_TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActive(tab.key)}
            className={active === tab.key ? "bg-white text-black px-4 py-2 rounded-lg" : "bg-card px-4 py-2 rounded-lg"}
          >
            {tab.label}
          </button>
        ))}
      </nav>
      {VIEW_BY_TAB[active]}
    </div>
  );
}
```

`frontend/src/components/workbench/ResearchCenter.tsx`

```tsx
import MarketPanel from "@/components/MarketPanel";
import ScreenerPanel from "@/components/ScreenerPanel";
import CryptoPanel from "@/components/CryptoPanel";

export default function ResearchCenter() {
  return (
    <div className="space-y-6">
      <MarketPanel />
      <ScreenerPanel />
      <CryptoPanel />
    </div>
  );
}
```

`frontend/src/components/workbench/StrategyLibrary.tsx`

```tsx
import StrategyWorkshop from "@/components/StrategyWorkshop";

export default function StrategyLibrary() {
  return <StrategyWorkshop />;
}
```

`frontend/src/components/workbench/ValidationCenter.tsx`

```tsx
import ValidationLab from "@/components/ValidationLab";

export default function ValidationCenter() {
  return <ValidationLab />;
}
```

`frontend/src/components/workbench/RunCenter.tsx`

```tsx
import PaperTradingPanel from "@/components/PaperTradingPanel";
import TradingPanel from "@/components/TradingPanel";

export default function RunCenter() {
  return (
    <div className="space-y-6">
      <PaperTradingPanel />
      <TradingPanel />
    </div>
  );
}
```

`frontend/src/components/workbench/RiskReviewCenter.tsx`

```tsx
import PortfolioPanel from "@/components/PortfolioPanel";
import BacktestPanel from "@/components/BacktestPanel";

export default function RiskReviewCenter() {
  return (
    <div className="space-y-6">
      <PortfolioPanel />
      <BacktestPanel />
    </div>
  );
}
```

`frontend/src/App.tsx`

```tsx
import WorkbenchShell from "./components/workbench/WorkbenchShell";

export default function App() {
  return (
    <Suspense fallback={<div className="p-6 text-sm text-[#8b949e]">加载 QuantPilot 工作台…</div>}>
      <WorkbenchShell />
    </Suspense>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && node --test --experimental-strip-types src/workbench/sections.test.ts && npm run type-check`  
Expected: PASS with the sections test green and `tsc --noEmit` exiting `0`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/workbench/sections.ts frontend/src/workbench/sections.test.ts frontend/src/components/workbench/WorkbenchShell.tsx frontend/src/components/workbench/ResearchCenter.tsx frontend/src/components/workbench/StrategyLibrary.tsx frontend/src/components/workbench/ValidationCenter.tsx frontend/src/components/workbench/RunCenter.tsx frontend/src/components/workbench/RiskReviewCenter.tsx frontend/src/App.tsx
git commit -m "feat: reshape frontend into workflow-first workbench"
```

### Task 3: Sync user-facing docs to the new workbench information architecture

**Files:**
- Modify: `docs/tab-pages-guide.md`
- Modify: `docs/DESIGN.md`
- Test: `frontend/src/workbench/navigation.test.ts`

- [ ] **Step 1: Extend the failing test to lock the new labels**

```ts
import test from "node:test";
import assert from "node:assert/strict";

import { WORKBENCH_TABS } from "./navigation.ts";

test("workbench labels match the workflow-first IA", () => {
  assert.deepEqual(
    WORKBENCH_TABS.map((tab) => tab.label),
    ["研究中心", "策略库", "验证中心", "运行中心", "风险与复盘"],
  );
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && node --test --experimental-strip-types src/workbench/navigation.test.ts`  
Expected: FAIL until the labels are updated to the new IA

- [ ] **Step 3: Write minimal implementation**

`docs/tab-pages-guide.md`

```md
## 主工作台结构（新版）

- 研究中心：看盘、选股/选币、候选池研究
- 策略库：策略编写、版本、模板、策略资产管理
- 验证中心：回测、样本外验证、参数实验、晋升判断
- 运行中心：模拟盘、实盘、订单、执行状态
- 风险与复盘：组合风险、回撤、熔断、复盘结论
```

`docs/DESIGN.md`

```md
### QuantPilot 工作台 IA（重构后）

顶层不再按专题能力组织，而按赚钱工作流组织：
1. 研究中心
2. 策略库
3. 验证中心
4. 运行中心
5. 风险与复盘
```

`frontend/src/workbench/navigation.ts`

```ts
export const WORKBENCH_TABS: WorkbenchTabDef[] = [
  { key: "research", label: "研究中心", icon: Activity },
  { key: "strategy", label: "策略库", icon: BookOpen },
  { key: "validation", label: "验证中心", icon: FlaskConical },
  { key: "run", label: "运行中心", icon: PlayCircle },
  { key: "risk_review", label: "风险与复盘", icon: ShieldAlert },
];
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && node --test --experimental-strip-types src/workbench/navigation.test.ts && npm run type-check`  
Expected: PASS with updated workflow labels

- [ ] **Step 5: Commit**

```bash
git add docs/tab-pages-guide.md docs/DESIGN.md frontend/src/workbench/navigation.ts frontend/src/workbench/navigation.test.ts
git commit -m "docs: align workbench docs with workflow-first IA"
```
