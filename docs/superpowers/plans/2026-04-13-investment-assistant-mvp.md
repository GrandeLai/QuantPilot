# Investment Assistant MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an independent investment assistant product that can work without custom QuantPilot strategies, consumes the shared platform when available, and only produces structured recommendations in phase one.

**Architecture:** Add a dedicated assistant API surface inside the shared backend and create a separate frontend app in `assistant_frontend/` that talks to those endpoints. The assistant uses shared platform facts for portfolio/risk/review data and emits structured advice cards instead of direct order actions.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, React 19, TypeScript, Vite, Zustand, existing QuantPilot backend modules

---

## File Map

- Create `backend/src/quantpilot/platform/advisor_service.py` — assistant read-model assembly
- Create `backend/src/quantpilot/api/advisor.py` — assistant endpoints
- Modify `backend/src/quantpilot/main.py` — register advisor router
- Create `backend/tests/test_advisor_api.py` — API contract tests
- Create `assistant_frontend/package.json` — independent app package definition
- Create `assistant_frontend/tsconfig.json` — TypeScript config
- Create `assistant_frontend/vite.config.ts` — dev server config
- Create `assistant_frontend/index.html` — app entry HTML
- Create `assistant_frontend/src/main.tsx` — app bootstrap
- Create `assistant_frontend/src/App.tsx` — assistant shell
- Create `assistant_frontend/src/api/client.ts` — assistant API client
- Create `assistant_frontend/src/store/advisorStore.ts` — assistant state store
- Create `assistant_frontend/src/navigation.ts` — product tabs
- Create `assistant_frontend/src/navigation.test.ts` — navigation regression test
- Create `assistant_frontend/src/components/PortfolioOverview.tsx`
- Create `assistant_frontend/src/components/OpportunityPool.tsx`
- Create `assistant_frontend/src/components/RebalanceSuggestions.tsx`
- Create `assistant_frontend/src/components/RiskRadar.tsx`
- Create `assistant_frontend/src/components/ReviewAsk.tsx`
- Modify `README.md` — document the new assistant app
- Modify `docs/DESIGN.md` — document the second product and new root directory

### Task 1: Expose assistant-ready API endpoints from the shared backend

**Files:**
- Create: `backend/src/quantpilot/platform/advisor_service.py`
- Create: `backend/src/quantpilot/api/advisor.py`
- Modify: `backend/src/quantpilot/main.py`
- Test: `backend/tests/test_advisor_api.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient


def test_advisor_overview_returns_structured_snapshot(client: TestClient) -> None:
    response = client.get("/api/advisor/overview")
    assert response.status_code == 200

    body = response.json()
    assert {"net_worth", "cash_ratio", "positions", "generated_at"} <= body.keys()


def test_advisor_opportunities_return_advice_cards(client: TestClient) -> None:
    response = client.get("/api/advisor/opportunities")
    assert response.status_code == 200

    body = response.json()
    assert isinstance(body["items"], list)
    if body["items"]:
        first = body["items"][0]
        assert {"type", "subject", "recommendation", "confidence", "evidence"} <= first.keys()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_advisor_api.py -v`  
Expected: FAIL with `404 != 200`

- [ ] **Step 3: Write minimal implementation**

`backend/src/quantpilot/platform/advisor_service.py`

```python
"""Read models for the investment assistant product."""

from __future__ import annotations

from datetime import datetime, timezone

from quantpilot.platform.agent_models import AdviceCard, AdviceEvidence


def build_overview_snapshot() -> dict:
    """Return a lightweight portfolio overview snapshot."""
    now = datetime.now(timezone.utc)
    return {
        "net_worth": 100000.0,
        "cash_ratio": 0.35,
        "positions": [],
        "generated_at": now,
    }


def build_opportunity_cards() -> list[AdviceCard]:
    """Return assistant opportunity cards."""
    now = datetime.now(timezone.utc)
    return [
        AdviceCard(
            type="opportunity",
            subject="AAPL",
            recommendation="watch",
            confidence=0.68,
            evidence=[
                AdviceEvidence(
                    source="market_data",
                    summary="relative strength is improving against recent range",
                    observed_at=now,
                )
            ],
            risk_notes=["earnings event risk remains elevated"],
            generated_at=now,
            freshness="fresh",
        )
    ]
```

`backend/src/quantpilot/api/advisor.py`

```python
"""Investment assistant API endpoints."""

from fastapi import APIRouter

from quantpilot.platform.advisor_service import build_opportunity_cards, build_overview_snapshot

router = APIRouter(prefix="/advisor", tags=["advisor"])


@router.get("/overview")
async def get_advisor_overview() -> dict:
    """Return an assistant-ready portfolio overview."""
    return build_overview_snapshot()


@router.get("/opportunities")
async def get_advisor_opportunities() -> dict:
    """Return assistant opportunity cards."""
    return {"items": [card.model_dump() for card in build_opportunity_cards()]}
```

`backend/src/quantpilot/main.py`

```python
from quantpilot.api.advisor import router as advisor_router

include_with_api_alias(advisor_router)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_advisor_api.py -v`  
Expected: PASS with `2 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/src/quantpilot/platform/advisor_service.py backend/src/quantpilot/api/advisor.py backend/src/quantpilot/main.py backend/tests/test_advisor_api.py
git commit -m "feat: add investment assistant api surface"
```

### Task 2: Scaffold a separate frontend app for the investment assistant

**Files:**
- Create: `assistant_frontend/package.json`
- Create: `assistant_frontend/tsconfig.json`
- Create: `assistant_frontend/vite.config.ts`
- Create: `assistant_frontend/index.html`
- Create: `assistant_frontend/src/main.tsx`
- Create: `assistant_frontend/src/navigation.ts`
- Test: `assistant_frontend/src/navigation.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
import test from "node:test";
import assert from "node:assert/strict";

import { ASSISTANT_TABS } from "./navigation.ts";

test("assistant tabs match the decision flow IA", () => {
  assert.deepEqual(
    ASSISTANT_TABS.map((tab) => tab.key),
    ["overview", "opportunities", "rebalance", "risk", "review"],
  );
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd assistant_frontend && node --test --experimental-strip-types src/navigation.test.ts`  
Expected: FAIL with `No such file or directory` or missing module errors

- [ ] **Step 3: Write minimal implementation**

`assistant_frontend/package.json`

```json
{
  "name": "quantpilot-investment-assistant",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "zustand": "^4.5.2",
    "lucide-react": "^1.8.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^6.0.0",
    "typescript": "^5.7.0",
    "vite": "^8.0.0"
  }
}
```

`assistant_frontend/src/navigation.ts`

```ts
export type AssistantTab =
  | "overview"
  | "opportunities"
  | "rebalance"
  | "risk"
  | "review";

export const ASSISTANT_TABS = [
  { key: "overview", label: "资产总览" },
  { key: "opportunities", label: "机会池" },
  { key: "rebalance", label: "调仓建议" },
  { key: "risk", label: "风险雷达" },
  { key: "review", label: "复盘与问答" },
] as const;
```

`assistant_frontend/src/main.tsx`

```tsx
import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd assistant_frontend && npm install && node --test --experimental-strip-types src/navigation.test.ts && npm run type-check`  
Expected: PASS with navigation test green and TypeScript exit code `0`

- [ ] **Step 5: Commit**

```bash
git add assistant_frontend/package.json assistant_frontend/tsconfig.json assistant_frontend/vite.config.ts assistant_frontend/index.html assistant_frontend/src/main.tsx assistant_frontend/src/navigation.ts assistant_frontend/src/navigation.test.ts
git commit -m "feat: scaffold investment assistant frontend"
```

### Task 3: Implement the assistant shell, state, and five core decision views

**Files:**
- Create: `assistant_frontend/src/App.tsx`
- Create: `assistant_frontend/src/api/client.ts`
- Create: `assistant_frontend/src/store/advisorStore.ts`
- Create: `assistant_frontend/src/components/PortfolioOverview.tsx`
- Create: `assistant_frontend/src/components/OpportunityPool.tsx`
- Create: `assistant_frontend/src/components/RebalanceSuggestions.tsx`
- Create: `assistant_frontend/src/components/RiskRadar.tsx`
- Create: `assistant_frontend/src/components/ReviewAsk.tsx`
- Modify: `README.md`
- Modify: `docs/DESIGN.md`
- Test: `assistant_frontend/src/navigation.test.ts`

- [ ] **Step 1: Extend the failing test to lock the labels**

```ts
import test from "node:test";
import assert from "node:assert/strict";

import { ASSISTANT_TABS } from "./navigation.ts";

test("assistant labels stay aligned with the decision flow", () => {
  assert.deepEqual(
    ASSISTANT_TABS.map((tab) => tab.label),
    ["资产总览", "机会池", "调仓建议", "风险雷达", "复盘与问答"],
  );
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd assistant_frontend && node --test --experimental-strip-types src/navigation.test.ts`  
Expected: FAIL until navigation labels match the final assistant IA

- [ ] **Step 3: Write minimal implementation**

`assistant_frontend/src/api/client.ts`

```ts
const BASE = "/api";

export async function fetchOverview() {
  const res = await fetch(`${BASE}/advisor/overview`);
  if (!res.ok) throw new Error("获取资产总览失败");
  return res.json();
}

export async function fetchOpportunities() {
  const res = await fetch(`${BASE}/advisor/opportunities`);
  if (!res.ok) throw new Error("获取机会池失败");
  return res.json();
}
```

`assistant_frontend/src/store/advisorStore.ts`

```ts
import { create } from "zustand";

interface AdvisorState {
  activeTab: "overview" | "opportunities" | "rebalance" | "risk" | "review";
  setActiveTab: (tab: AdvisorState["activeTab"]) => void;
}

export const useAdvisorStore = create<AdvisorState>((set) => ({
  activeTab: "overview",
  setActiveTab: (activeTab) => set({ activeTab }),
}));
```

`assistant_frontend/src/App.tsx`

```tsx
import { useMemo } from "react";

import { ASSISTANT_TABS } from "./navigation";
import { useAdvisorStore } from "./store/advisorStore";
import PortfolioOverview from "./components/PortfolioOverview";
import OpportunityPool from "./components/OpportunityPool";
import RebalanceSuggestions from "./components/RebalanceSuggestions";
import RiskRadar from "./components/RiskRadar";
import ReviewAsk from "./components/ReviewAsk";

export default function App() {
  const activeTab = useAdvisorStore((state) => state.activeTab);
  const setActiveTab = useAdvisorStore((state) => state.setActiveTab);

  const currentView = useMemo(() => {
    switch (activeTab) {
      case "overview":
        return <PortfolioOverview />;
      case "opportunities":
        return <OpportunityPool />;
      case "rebalance":
        return <RebalanceSuggestions />;
      case "risk":
        return <RiskRadar />;
      case "review":
        return <ReviewAsk />;
    }
  }, [activeTab]);

  return (
    <div className="min-h-screen bg-[#0d1117] text-white">
      <header className="px-6 py-4 border-b border-[#30363d]">
        <h1 className="text-xl font-semibold">个人投资助理</h1>
      </header>
      <nav className="flex gap-2 px-6 py-4">
        {ASSISTANT_TABS.map((tab) => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)} className="px-3 py-2 rounded-lg bg-[#161b22]">
            {tab.label}
          </button>
        ))}
      </nav>
      <main className="px-6 pb-8">{currentView}</main>
    </div>
  );
}
```

`README.md`

```md
## 产品结构

- `frontend/`：QuantPilot 量化交易工作台
- `assistant_frontend/`：个人投资助理独立前端
- `backend/`：两个产品共享的后端与平台能力
```

`docs/DESIGN.md`

```md
### 产品分层（重构后）

- QuantPilot：主产品，量化交易工作台
- 个人投资助理：独立产品，负责机会、配置、风险和复盘建议
- 共享平台层：数据、验证、执行、风险、Agent
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd assistant_frontend && node --test --experimental-strip-types src/navigation.test.ts && npm run type-check && npm run build`  
Expected: PASS with assistant navigation labels locked and the new frontend building successfully

- [ ] **Step 5: Commit**

```bash
git add assistant_frontend/src/App.tsx assistant_frontend/src/api/client.ts assistant_frontend/src/store/advisorStore.ts assistant_frontend/src/components/PortfolioOverview.tsx assistant_frontend/src/components/OpportunityPool.tsx assistant_frontend/src/components/RebalanceSuggestions.tsx assistant_frontend/src/components/RiskRadar.tsx assistant_frontend/src/components/ReviewAsk.tsx README.md docs/DESIGN.md
git commit -m "feat: add investment assistant mvp frontend"
```
