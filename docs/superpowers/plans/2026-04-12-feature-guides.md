# Feature Guide Overlay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable floating help button and animated modal that exposes plain-language, step-by-step operating guides for every top-level tab and nested feature area in the frontend.

**Architecture:** Use a single config-driven guide registry keyed by stable feature ids. Reusable UI components render a floating help trigger and a shared animated modal, while pages opt in by placing guide anchors on the active region or feature block.

**Tech Stack:** React 19, TypeScript, Tailwind CSS v4, `motion`, Node built-in `node:test`

---

## File Map

- Create: `frontend/src/content/featureGuides.ts`
- Create: `frontend/src/components/guides/FeatureGuideButton.tsx`
- Create: `frontend/src/components/guides/FeatureGuideModal.tsx`
- Create: `frontend/src/components/guides/guideTypes.ts`
- Create: `frontend/src/content/featureGuides.test.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/MarketPanel.tsx`
- Modify: `frontend/src/components/TradingPanel.tsx`
- Modify: `frontend/src/components/PaperTradingPanel.tsx`
- Modify: `frontend/src/components/BacktestPanel.tsx`
- Modify: `frontend/src/components/OptionsGreeksPanel.tsx`
- Modify: `frontend/src/components/AIPanel.tsx`
- Modify: `frontend/src/components/SystemPanel.tsx`
- Modify: `frontend/src/components/ScreenerPanel.tsx`
- Modify: `frontend/src/components/StrategyWorkshop.tsx`
- Modify: `frontend/src/components/chart/ChartMainArea.tsx`
- Modify: `frontend/src/components/chart/ChartWatchlist.tsx`
- Modify: `frontend/src/components/chart/ChartOrderEntry.tsx`
- Modify: `frontend/src/components/chart/ChartBottomPanels.tsx`
- Modify: `frontend/src/index.css`
- Modify: `docs/DESIGN.md`

## Tasks

### Task 1: Define guide content model and coverage

- [ ] Add typed guide data structures for titles, summaries, steps, quick tips, and coverage metadata.
- [ ] Create a central guide registry covering top-level tabs, nested sub-tabs, and major visible feature blocks.
- [ ] Add helper exports that list all guide keys for test coverage and safe lookups.

### Task 2: Build reusable guide UI

- [ ] Create a floating help button component that can be attached to any relative container.
- [ ] Create a shared modal with entry/exit animation, backdrop, keyboard dismissal, and scrollable step-by-step content.
- [ ] Add small shared CSS helpers for subtle pulse/float motion and modal polish where utility classes are not enough.

### Task 3: Integrate guides into panels

- [ ] Add one top-level guide trigger to each primary workspace tab.
- [ ] Add guide triggers for nested sub-tabs such as market, AI, system, strategy workshop, trading, screener, and options views.
- [ ] Add focused feature-block guides inside complex views, especially chart layout and paper trading account detail sections.

### Task 4: Add regression checks

- [ ] Add a `node:test` coverage test that verifies all expected feature ids exist in the guide registry and that every guide has at least one step.
- [ ] Run the test directly with Node’s TypeScript support to confirm the registry is syntactically valid and complete.

### Task 5: Update design docs and verify

- [ ] Record the frontend guide-overlay enhancement in `docs/DESIGN.md`.
- [ ] Run build, type-check, and the new guide test.
- [ ] Fix any regressions before reporting completion.
