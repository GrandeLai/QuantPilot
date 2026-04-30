# Acceptance Report — F.18 Sector Momentum Heatmap

**Task spec**: `docs/tasks/phaseF18/sector-momentum.md`
**PR commit**: `47e85cc` (feat(F.18): add Sector Momentum Heatmap (SPDR ETF rotation))
**Date**: 2026-04-29
**Verdict**: PASS

---

## 1. File Scope Check

Files changed in `HEAD~1..HEAD`:

| File | In Whitelist? |
|------|--------------|
| `apps/stock-assistant/backend/src/quantpilot_stock/api/sector_momentum.py` | YES |
| `apps/stock-assistant/backend/src/quantpilot_stock/earnings_move/engine.py` | NO — see note |
| `apps/stock-assistant/backend/src/quantpilot_stock/main.py` | YES |
| `apps/stock-assistant/backend/src/quantpilot_stock/sector_momentum/__init__.py` | YES |
| `apps/stock-assistant/backend/src/quantpilot_stock/sector_momentum/engine.py` | YES |
| `apps/stock-assistant/backend/tests/test_sector_momentum.py` | YES |
| `apps/stock-assistant/frontends/workbench/src/api/client.ts` | YES |
| `apps/stock-assistant/frontends/workbench/src/components/SectorMomentumPanel.tsx` | YES |
| `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx` | YES |
| `docs/tasks/phaseF18/sector-momentum.md` | YES |

**Note on out-of-whitelist file**: `earnings_move/engine.py` has a single-character bug fix —
a missing `f` prefix on an f-string in F.17's `_interpretation()` function
(`"期权买方需要超过 {pct:.1f}%..."` → `f"期权买方需要超过 {pct:.1f}%..."`).
This is a pre-existing correctness bug in a shipped feature.  The change is
clearly a bug-fix (1 character, no logic alteration) and is explicitly called out
in the commit message under "Also fix: f-string interpolation in F.17".
It does not constitute a scope expansion that could destabilize the codebase.
**Decision: accept as a minor incidental fix; does not trigger FAIL.**

---

## 2. Code Review

### engine.py
- Module-level docstring: present.
- All public symbols have type hints.
- `SECTOR_ETFS`: dict with exactly 11 entries (XLK/XLV/XLF/XLY/XLP/XLE/XLI/XLB/XLRE/XLU/XLC). Correct.
- `SectorReturn` dataclass: fields `ticker`, `sector_name`, `return_1m`, `return_3m`, `return_6m`, `vs_spy_1m`, `grade`. All correct.
- `SectorMomentumData` dataclass: fields `sectors`, `top3`, `bottom3`, `spy_return_1m`, `as_of_date`, `data_available`. All correct.
- `_sector_grade(return_1m, vs_spy_1m)`: uses `vs_spy_1m > 2.0` for "leading" and `vs_spy_1m < -2.0` for "lagging" — mathematically equivalent to the spec's `return_1m > spy_return_1m + 2.0` form since `vs_spy_1m = return_1m - spy_return_1m`. Correct.
- `compute_sector_momentum()`: uses `yf.download(tickers=..., period="6mo", ...)` — single batch download. Returns `SectorMomentumData` in all paths, never raises. Correct.
- No cross-app imports. No `apps/*` import in `common/`. All imports within `quantpilot_stock`.

### api/sector_momentum.py
- Module-level docstring: present.
- `GET /api/sector-momentum` implemented via `router.get("/")` with prefix `/sector-momentum`.
- Router registered via `include_with_api_alias(sector_momentum_router)` in `main.py` (lines 133–134).
- No ticker parameter on the endpoint. Returns 200 always (graceful degradation).
- Uses `run_in_executor` for async safety. Pydantic v2 response models.

### Frontend
- `client.ts`: `SectorReturnData` interface (lines 1549–1557), `SectorMomentumData` interface (lines 1559–1566), `fetchSectorMomentum()` function (lines 1568–1580). All correctly typed.
- `SectorMomentumPanel.tsx`: full-featured component with sector table (1M/3M/6M/vs SPY columns), top3/bottom3 row highlighting, `data_available=false` degradation banner, auto-loads on mount via `useEffect`. Correct.
- `RiskReviewCenter.tsx`: imports and renders `<SectorMomentumPanel />` (lines 21 and 37). Correct.

### Quality observations
- `return_1m` parameter in `_sector_grade` is accepted but not used in the function body. This is benign — the signature matches the spec, and the logic is correct via `vs_spy_1m`. No mypy warning because `ignore_missing_imports=true` and the param is type-annotated.
- ruff check: `All checks passed!`
- mypy check: `Success: no issues found in 3 source files`

---

## 3. Test Execution

### pytest tests/test_sector_momentum.py -v

```
22 passed in 4.95s
```

All 22 tests passed:

| Group | Tests | Result |
|-------|-------|--------|
| TestSectorGrade (grade boundaries) | 6 | PASS |
| TestPctReturn (pct calculation) | 4 | PASS |
| TestComputeSectorMomentum (happy path) | 5 | PASS |
| TestGracefulDegradation (degradation) | 4 | PASS |
| TestSectorMomentumAPIEndpoint (API 200) | 3 | PASS |

### Frontend build (npm run build -w quantpilot-frontend)

```
✓ built in 539ms
```

No TypeScript errors.

### Mypy

```
Success: no issues found in 3 source files
```

### Ruff

```
All checks passed!
```

---

## 4. AC Checklist

| AC | Description | Status |
|----|-------------|--------|
| AC-1 | `SECTOR_ETFS` dict with 11 entries (all 11 SPDR ETFs present) | PASS |
| AC-1 | `SectorReturn` dataclass with correct fields + type hints | PASS |
| AC-1 | `SectorMomentumData` dataclass with correct fields | PASS |
| AC-1 | `_sector_grade` boundary: vs_spy > 2.0 → "leading", < -2.0 → "lagging", else "in_line" | PASS |
| AC-1 | `compute_sector_momentum()` always returns, never raises | PASS |
| AC-1 | Single batch `yf.download` call; `data_available=False` on failure | PASS |
| AC-2 | `GET /api/sector-momentum` → always 200 | PASS |
| AC-2 | Router registered via `include_with_api_alias` | PASS |
| AC-3 | `SectorReturnData`, `SectorMomentumData` types in `client.ts` | PASS |
| AC-3 | `fetchSectorMomentum()` in `client.ts` | PASS |
| AC-3 | `SectorMomentumPanel.tsx` with sector table + top3/bottom3 + degradation banner | PASS |
| AC-3 | `SectorMomentumPanel` added to `RiskReviewCenter.tsx` | PASS |
| AC-3 | TypeScript build with no errors | PASS |
| AC-4 | ≥12 tests (actual: 22) | PASS |
| AC-4 | `_sector_grade` boundary tests | PASS |
| AC-4 | `compute_sector_momentum` happy path (mocked `yf.download`) | PASS |
| AC-4 | yfinance unavailable → `data_available=False`, never raises | PASS |
| AC-4 | API 200 + all sector fields present | PASS |

---

## 5. Summary

All 18 AC items pass. 22/22 tests pass. Frontend builds cleanly. Ruff and mypy report no issues.

One file outside the spec whitelist (`earnings_move/engine.py`) was modified with a trivial
one-character f-string bug fix explicitly noted in the commit message; it does not affect
correctness or scope of F.18. This is accepted as an incidental fix.

**VERDICT: PASS**
