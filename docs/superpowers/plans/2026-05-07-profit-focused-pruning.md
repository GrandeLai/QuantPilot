# Profit-Focused Pruning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove code paths that do not directly support the product mission: help the user make money or avoid avoidable losses.

**Architecture:** Keep `quant-assistant` as the strategy research/validation engine and `stock-assistant` as the decision assistant/execution surface. Remove standalone feature islands and collapse technical analysis into a small evidence layer consumed by recommendations, risk review, and opportunity ranking.

**Tech Stack:** Python/FastAPI/Pydantic/pytest/ruff/mypy, Rust/axum/cargo, React/TypeScript/Vite, shared `common/` contracts.

---

## Validation Rule

Every task has a verification phase. Do not proceed to the next task until its verification phase passes or the failure is explicitly accepted and documented.

## Task 1: Remove Plugin Ecosystem

**Why:** Runtime plugins are platform/ecosystem infrastructure. They do not directly improve opportunity selection, risk control, execution, or post-trade review.

**Files:**
- Delete: `common/python/quantpilot_common/plugins/`
- Delete: `apps/stock-assistant/backend/src/quantpilot_stock/api/plugins.py`
- Modify: `apps/stock-assistant/backend/src/quantpilot_stock/main.py`
- Modify: `apps/stock-assistant/backend/tests/test_frontend_contracts.py`
- Modify: `common/python/pyproject.toml`
- Modify: `docs/DESIGN.md`
- Modify: `docs/architecture/features.md`
- Modify: `docs/architecture/stock-assistant-api.md`

**Verification Phase:**

```bash
(cd common/python && uv run pytest tests/test_plugins.py -q)
```

Expected before deletion: plugin tests pass and prove the code exists.

After deletion, remove `tests/test_plugins.py`, then run:

```bash
(cd common/python && uv run pytest tests/ -q)
(cd apps/stock-assistant/backend && uv run pytest tests/test_frontend_contracts.py -q)
(cd common/python && uv run ruff check quantpilot_common tests)
(cd apps/stock-assistant/backend && uv run ruff check src tests)
(cd common/python && uv run mypy quantpilot_common)
rg -n "plugins|/api/plugins|quantpilot_common.plugins" common apps docs
```

Expected after deletion: tests/lint/typecheck pass; grep only finds archived migration/history references or no live references.

## Task 2: Remove Generic LLM Chat And Strategy Generation

**Why:** Generic chat and strategy generation are not reliable money-making surfaces. Keep advisor/agent internals only if they produce structured, evidence-backed recommendations.

**Files:**
- Delete: `apps/stock-assistant/backend/src/quantpilot_stock/api/llm.py`
- Delete: `apps/stock-assistant/backend/src/quantpilot_stock/llm/`
- Delete: `apps/stock-assistant/backend/tests/test_llm.py`
- Delete: `apps/stock-assistant/backend/tests/test_llm_strategy_gen.py`
- Delete: `apps/stock-assistant/backend/tests/test_litellm.py`
- Modify: `apps/stock-assistant/backend/src/quantpilot_stock/main.py`
- Modify: `apps/stock-assistant/frontends/workbench/src/components/StrategyGeneratorPanel.tsx` (delete if only caller)
- Modify: `apps/stock-assistant/backend/pyproject.toml` (remove `litellm` only after agent/advisor no longer imports it)
- Modify: docs API/feature references.

**Verification Phase:**

```bash
rg -n "/api/llm|quantpilot_stock.llm|litellm|StrategyGenerator" apps common docs
(cd apps/stock-assistant/backend && uv run pytest tests/agent tests/test_advisor.py tests/test_frontend_contracts.py -q)
(cd apps/stock-assistant/backend && uv run ruff check src tests)
(cd apps/stock-assistant/backend && uv run mypy src/quantpilot_stock)
(cd apps/stock-assistant/frontends/workbench && npm run build)
(cd apps/stock-assistant/frontends/assistant && npm run build)
```

Expected: no live `/api/llm` or strategy-generator references remain; advisor tests still pass or are rewritten to a non-LLM deterministic recommendation stub.

## Task 3: Collapse Technical Indicator Islands

**Why:** Dozens of one-indicator modules are noise. Keep one market-structure evidence service and one UI panel.

**Keep or merge into `technical_score`:**
- Trend: `ma_alignment`, `macd`, `supertrend`
- Momentum: `rsi_signal`, `roc`
- Volume: `obv`, `mfi`, `vroc`
- Volatility: `atr`, `bollinger`
- Support/resistance: `pivot_points`, `vwap`
- Aggregate: `technical_score`

**Delete standalone modules and panels:**
- Backend/API/tests/panels for `adx_trend`, `alligator`, `aroon`, `awesome_osc`, `cci`, `chaikin_osc`, `chaikin_vol`, `choppiness`, `cks`, `cmf`, `cmo`, `connors_rsi`, `dema`, `donchian`, `dpo`, `elder_impulse`, `elder_ray`, `fisher_transform`, `force_index`, `hma`, `ichimoku`, `kama`, `keltner`, `kst`, `kvo`, `mass_index`, `ppo`, `price_osc`, `pvt`, `sar`, `stc`, `stoch_rsi`, `stochastic`, `tema`, `trix`, `tsi`, `ultimate_osc`, `vortex`, `williams_r`.

**Files:**
- Modify: `apps/stock-assistant/backend/src/quantpilot_stock/main.py`
- Modify: `apps/stock-assistant/frontends/workbench/src/api/client.ts`
- Replace: `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
- Keep/refactor: `apps/stock-assistant/backend/src/quantpilot_stock/technical_score/`
- Keep/refactor: `apps/stock-assistant/frontends/workbench/src/components/TechnicalScorePanel.tsx`

**Verification Phase:**

```bash
(cd apps/stock-assistant/backend && uv run pytest tests/test_technical_score.py tests/test_ma_alignment.py tests/test_macd.py tests/test_rsi_signal.py tests/test_roc.py tests/test_obv.py tests/test_mfi.py tests/test_vroc.py tests/test_atr.py tests/test_bollinger.py tests/test_pivot_points.py tests/test_vwap.py -q)
(cd apps/stock-assistant/backend && uv run ruff check src tests)
(cd apps/stock-assistant/backend && uv run mypy src/quantpilot_stock)
(cd apps/stock-assistant/frontends/workbench && npm run build)
rg -n "ADXTrendPanel|AlligatorPanel|AroonPanel|AwesomeOscPanel|WilliamsRPanel|TRIXPanel|VortexPanel" apps/stock-assistant/frontends/workbench/src apps/stock-assistant/backend/src
```

Expected: retained aggregate technical evidence passes; deleted indicator names have no live references.

## Task 4: Collapse Fundamental/Event/Crypto Evidence Into Recommendation Inputs

**Why:** These can help make money, but not as independent page islands. They should be evidence providers for opportunity, rebalance, and risk recommendations.

**Keep as evidence providers:**
- `fundamental`, `dcf`, `earnings_quality`, `eps_revision`, `analyst_consensus`
- `sec`, `insider_trading`, `short_interest`, `earnings_calendar`, `earnings_move`
- `crypto_derivs`, `token_unlock`, `crypto_whale`
- `gex`, `iv_rank`, `put_call_ratio`, `max_pain`

**Delete standalone RiskReviewCenter panels after evidence integration:**
- `FundamentalPanel`, `DCFPanel`, `EarningsQualityPanel`, `EPSRevisionPanel`, `AnalystConsensusPanel`, `SECEventsPanel`, `InsiderTradingPanel`, `ShortInterestPanel`, `EarningsCalendarPanel`, `EarningsMovePanel`, `CryptoDerivsPanel`, `TokenUnlockPanel`, `WhaleMonitorPanel`, `GEXPanel`, `IVRankPanel`, `PutCallRatioPanel`, `MaxPainPanel`.

**Verification Phase:**

```bash
(cd apps/stock-assistant/backend && uv run pytest tests/test_advisor.py tests/test_dcf_api.py tests/test_fundamental_api.py tests/test_eps_revision_api.py tests/test_sec_api.py tests/test_crypto_derivs_api.py tests/test_options_gex_api.py tests/test_token_unlock_api.py -q)
(cd apps/stock-assistant/frontends/assistant && npm run build)
(cd apps/stock-assistant/frontends/workbench && npm run build)
```

Expected: advisor/recommendation flows still receive evidence, but standalone panel imports are gone.

## Task 5: Remove Sample Applications And Demo-Only Assets

**Why:** Samples are not the product and add maintenance surface.

**Files:**
- Delete: `sample/quantpilot-market-sentiment/`
- Delete: `sample/quantpilot-portfolio-manager/`
- Delete: `sample/quantpilot-studio/`
- Modify: root `package.json`
- Modify: root `package-lock.json`
- Modify docs references.

**Verification Phase:**

```bash
npm install --package-lock-only
npm run build --workspaces --if-present
rg -n "sample/quantpilot|quantpilot-studio|quantpilot-market-sentiment|quantpilot-portfolio-manager" .
```

Expected: no live sample references outside archived docs/history.

## Task 6: Final Product UI Unification Gate

**Why:** Deleting is not enough. Remaining UI must become one coherent product surface.

**Files:**
- Create or refactor shared UI primitives under `common/frontend-components/src/ui/`
- Modify stock workbench panels to use shared primitives
- Modify assistant shell to use same spacing, token colors, cards, loading/error states
- Modify quant frontend to share the same page shell and controls

**Verification Phase:**

```bash
(cd common/frontend-components && npm run build)
(cd apps/stock-assistant/frontends/workbench && npm run build)
(cd apps/stock-assistant/frontends/assistant && npm run build)
(cd apps/quant-assistant/frontend && npm run build)
rg -n "style=\\{\\{" apps/stock-assistant/frontends apps/quant-assistant/frontend common/frontend-components
```

Expected: builds pass; inline styles are eliminated or only remain in chart/canvas/SVG drawing code.

## Final Full Verification

Run after all tasks:

```bash
(cd common/python && uv run pytest tests/ -q)
(cd apps/stock-assistant/backend && uv run pytest tests/ -q)
(cd apps/quant-assistant/backend && cargo test)
(cd common/frontend-components && npm run build)
(cd apps/stock-assistant/frontends/workbench && npm run build)
(cd apps/stock-assistant/frontends/assistant && npm run build)
(cd apps/quant-assistant/frontend && npm run build)
rg -n "plugins|/api/plugins|/api/llm|StrategyGeneratorPanel|sample/quantpilot" apps common docs
git diff --check
```

Expected: all verification passes; any remaining grep hit must be in archive/history docs and explicitly listed in the final report.
