# Design: QuantPilot Documentation Overhaul (Phase A–E)

**Date**: 2026-04-28  
**Scope**: Update + create project documentation to reflect current two-app monorepo state after Phase A–E completion

---

## Context

The project has completed Phase A (monorepo split), Phase B (Rust MVP backtest), Phase C (API expansion: walk-forward, optimize, indicators), Phase D (HTTP API modularization + trade tracking), and Phase E (frontend wire-up). Most documentation still reflects the pre-split or Phase A state. The gap between docs and code creates confusion for onboarding and for LLM agents (like acceptance-agent) that read these files.

---

## Goals

1. Every major doc accurately reflects the current architecture and endpoints.
2. A developer (or LLM) reading docs alone can understand: how to run the project, what each app does, how the APIs are structured, how the frontend routes requests, and where the acceptance workflow lives.
3. No placeholder text, no references to deleted paths (quant-assistant-py, rust_core, legacy backend/).

---

## Files to Update

### `docs/DESIGN.md`
Complete rewrite. Current version describes the pre-split single-backend architecture. New version covers:
- Two-app overview (stock-assistant Python + quant-assistant Rust)
- Common layer structure
- Port assignments (8001, 8002, 5173, 5174, 5175)
- DuckDB write-discipline (stock-assistant writes, quant reads)
- Schema codegen pipeline
- Phase progression summary (A→E state)

### `README.md` (root)
Update to reflect:
- Current monorepo layout (apps/, common/, tools/)
- Quick-start commands for each app (dev-stock.sh, dev-quant.sh)
- Link to DESIGN.md, MIGRATION.md, CLAUDE.md
- Remove any references to old single-backend layout

### `CLAUDE.md`
Update the "常用命令" section:
- Add Phase D endpoints (POST /api/backtest/run, /api/walk-forward, /api/optimize, /api/indicators)
- Add quant-assistant frontend port (5175)
- Verify test commands are current

### `docs/MIGRATION.md`
Append entries for:
- Step 4 (quant-assistant-py deletion, 2026-04-27)
- Phase D (api-expand: src/api/ modularization + trade tracking)
- Phase E (frontend-wired: quant research frontend connected to Rust API)

### `docs/protocols/duckdb-write-discipline.md`
Minor accuracy check; add note that quant-assistant results.duckdb (if created in future) is separate from market.duckdb.

### `docs/conventions/acceptance-process.md`
Minor update: clarify that NEEDS-REVISION due to spec whitelist omission (not scope creep) can be resolved by updating the task spec and re-running acceptance-agent.

---

## Files to Create

### `docs/architecture/quant-assistant-api.md`
Rust HTTP API reference covering all 5 endpoints:
- `GET /healthz` — liveness check
- `POST /api/backtest/run` — MA crossover backtest, full metrics + trade stats
- `POST /api/walk-forward` — walk-forward validation splits
- `POST /api/optimize` — grid search over MA periods, returns top-N by Sharpe
- `POST /api/indicators` — SMA/EMA calculation over price series

Each endpoint documented with: request shape, response shape, example values, error conditions.

### `docs/architecture/frontend-routing.md`
Documents Vite dev proxy configuration:
- `/api/data/*` → stock-assistant (localhost:8001) — market data
- `/api/backtest/*`, `/api/walk-forward`, `/api/optimize`, `/api/indicators` → quant-assistant (localhost:8002)
- Production note: reverse proxy (nginx/caddy) needed for deployed builds

---

## Out of Scope

- No code changes
- No new features
- No changes to acceptance workflow tooling
- Does not cover future phases (A1 equity chart, A2 walk-forward panel, A3 ML endpoint)

---

## Acceptance Criteria

- AC-1: `grep -r "quant-assistant-py\|rust_core\|apps/backend" docs/ README.md CLAUDE.md` returns no hits on active content (only in MIGRATION.md as historical record)
- AC-2: `docs/architecture/quant-assistant-api.md` exists and lists all 5 endpoints
- AC-3: `docs/architecture/frontend-routing.md` exists and documents the proxy table
- AC-4: `CLAUDE.md` 常用命令 section mentions all 4 POST endpoints
- AC-5: `docs/DESIGN.md` mentions both `apps/stock-assistant` and `apps/quant-assistant` and their ports (8001, 8002)

---

## Implementation Order

1. Create `docs/architecture/` directory + two new files (no conflict risk)
2. Append `docs/MIGRATION.md` (additive only)
3. Update `docs/conventions/acceptance-process.md` (minor)
4. Update `docs/protocols/duckdb-write-discipline.md` (minor)
5. Update `CLAUDE.md` (targeted additions)
6. Rewrite `docs/DESIGN.md` (largest change, do last among updates)
7. Update `README.md`
