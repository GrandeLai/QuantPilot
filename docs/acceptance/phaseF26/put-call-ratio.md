# Acceptance Report — Task F.26: Put/Call Ratio & Options Sentiment

**Task ID**: phaseF26/put-call-ratio  
**Task Spec**: docs/tasks/phaseF26/put-call-ratio.md  
**Acceptance Agent Run Date**: 2026-04-30  
**Verdict**: PASS

---

## 1. File Scope Check

Changed files in latest commit vs whitelist:

| File | In Whitelist |
|---|---|
| apps/stock-assistant/backend/src/quantpilot_stock/api/put_call_ratio.py | YES |
| apps/stock-assistant/backend/src/quantpilot_stock/main.py | YES |
| apps/stock-assistant/backend/src/quantpilot_stock/put_call_ratio/__init__.py | YES |
| apps/stock-assistant/backend/src/quantpilot_stock/put_call_ratio/engine.py | YES |
| apps/stock-assistant/backend/tests/test_put_call_ratio.py | YES |
| apps/stock-assistant/frontends/workbench/src/api/client.ts | YES |
| apps/stock-assistant/frontends/workbench/src/components/PutCallRatioPanel.tsx | YES |
| apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx | YES |
| docs/tasks/phaseF26/put-call-ratio.md | YES |

**Result**: All 9 changed files are within the whitelist. No out-of-scope changes.

---

## 2. Code Review (Lightweight)

- **Docstrings**: engine.py has a module-level docstring. api/put_call_ratio.py has a module-level docstring. PutCallRatioPanel.tsx has a JSDoc block. All required files have appropriate documentation.
- **Type hints**: All Python functions have full type hints. `PCRSentiment` is a `Literal[...]` type. `ExpiryPCR` and `PCRData` are typed dataclasses with `float | None` fields correctly annotated.
- **No cross-app imports**: All imports stay within `quantpilot_stock.*` and standard libraries. No `quant-assistant` imports found.
- **No reverse imports from common**: `common/` is not imported anywhere in the changed files.
- **No scope creep**: Changes are strictly scoped to PCR functionality.
- **Dependency**: Only uses `yfinance`, `pandas`, `fastapi` — all already in the project's dependency set. No new external dependencies introduced.

---

## 3. Test Results

Command: `uv run pytest tests/test_put_call_ratio.py -v`

```
28 passed in 6.60s
```

All 28 tests passed. Test count (28) exceeds the AC-4 requirement of >= 16.

Test classes and coverage:
- `TestComputePcr` (4 tests): normal ratio, zero call returns None, zero put returns 0, equal put/call
- `TestClassifySentiment` (8 tests): all 5 sentiment bands + None + exact boundaries at 1.0 and 0.7
- `TestAggregateChain` (2 tests): normal aggregation, empty DataFrame
- `TestComputePutCallRatioNormal` (6 tests): data_available=True, volume_pcr, oi_pcr, expiry_breakdown, extreme_bearish, extreme_bullish
- `TestGracefulDegradation` (5 tests): no options, yfinance exception, chain error skipped, ticker uppercased, interpretation populated
- `TestPutCallRatioAPIEndpoint` (3 tests): 200 with ticker, 422 without ticker, 200 on network failure

All network calls are mocked via `unittest.mock.patch`.

---

## 4. Linting and Type Checking

### ruff check
Command: `uv run ruff check src/quantpilot_stock/put_call_ratio/ src/quantpilot_stock/api/put_call_ratio.py tests/test_put_call_ratio.py`

Result: **All checks passed!** (exit code 0)

### mypy
Command: `uv run mypy src/quantpilot_stock/put_call_ratio/ src/quantpilot_stock/api/put_call_ratio.py`

Result: **Success: no issues found in 3 source files** (exit code 0)

---

## 5. TypeScript and Build

### TypeScript (tsc --noEmit)
Command: `npx tsc --noEmit` (workbench)

Result: **No errors** (empty output, exit code 0)

### Vite Build
Command: `npx vite build` (workbench)

Result: **built in 396ms** — success (exit code 0)

---

## 6. AC-by-AC Verification

### AC-1: Data Model
- `PCRSentiment` = `Literal["extreme_bearish","bearish","neutral","bullish","extreme_bullish","unknown"]` — CONFIRMED in engine.py:26-33
- `ExpiryPCR` dataclass with all required fields (expiry, days_to_expiry, volume_pcr, oi_pcr, call_volume, put_volume, call_oi, put_oi) — CONFIRMED in engine.py:48-57
- `PCRData` dataclass with all required fields (ticker, volume_pcr, oi_pcr, total_call_volume, total_put_volume, total_call_oi, total_put_oi, expiry_breakdown, sentiment, interpretation, as_of_date, data_available) — CONFIRMED in engine.py:60-73

**Status: PASS**

### AC-2: Calculation Logic
- volume_pcr = total_put_volume / total_call_volume — CONFIRMED via `_compute_pcr(pv, cv)` in engine.py:242
- oi_pcr = total_put_oi / total_call_oi — CONFIRMED via `_compute_pcr(total_put_oi, total_call_oi)` in engine.py:243
- Sentiment thresholds:
  - >= 1.5 → extreme_bearish (CONFIRMED: `_EXTREME_BEARISH = 1.5`, test_extreme_bearish passes with pcr=1.6)
  - 1.0-1.5 → bearish (CONFIRMED: `_BEARISH = 1.0`, test_bearish passes with pcr=1.2, boundary test at 1.0 → bearish)
  - 0.7-1.0 → neutral (CONFIRMED: `_BULLISH = 0.7`, test_neutral passes with pcr=0.85, boundary test at 0.7 → neutral)
  - 0.5-0.7 → bullish (CONFIRMED: `_EXTREME_BULLISH = 0.5`, test_bullish passes with pcr=0.6)
  - < 0.5 → extreme_bullish (CONFIRMED: test_extreme_bullish passes with pcr=0.4)
- expiry_breakdown: each expiry processed individually with its own volume/OI PCR — CONFIRMED in engine.py:206-239

**Status: PASS**

### AC-3: Degradation Strategy
- No options → data_available=True, volume_pcr=None, sentiment=unknown — CONFIRMED in engine.py:182-196, test passes
- call volume = 0 → volume_pcr=None — CONFIRMED via `_compute_pcr` returning None when call_val <= 0, test_zero_call_returns_none passes
- yfinance completely fails → data_available=False — CONFIRMED in engine.py:272-274, test_yfinance_exception_returns_default passes

**Status: PASS**

### AC-4: Test Requirements
- Test count: 28 >= 16 — CONFIRMED
- _compute_pcr normal + zero protection + single-leg zero — CONFIRMED (TestComputePcr: 4 tests)
- compute_put_call_ratio normal with options — CONFIRMED (TestComputePutCallRatioNormal: 6 tests)
- PCR > 1.5 → extreme_bearish, < 0.5 → extreme_bullish — CONFIRMED (test_extreme_bearish_signal, test_extreme_bullish_signal)
- No options → data_available=True, sentiment=unknown — CONFIRMED (test_no_options_returns_unknown)
- yfinance exception → data_available=False — CONFIRMED (test_yfinance_exception_returns_default)
- expiry_breakdown correct aggregation — CONFIRMED (test_expiry_breakdown_populated, TestAggregateChain)
- API GET /api/put-call-ratio, no ticker 422, with ticker 200 — CONFIRMED (TestPutCallRatioAPIEndpoint: 3 tests)
- All tests mock network calls — CONFIRMED (all tests use `@patch("quantpilot_stock.put_call_ratio.engine.yf.Ticker")`)

**Status: PASS**

### AC-5: API
- Route `GET /api/put-call-ratio?ticker=<TICKER>` — CONFIRMED in api/put_call_ratio.py:9
- No ticker → HTTP 422 — CONFIRMED (Query(...) makes it required; test passes)
- With ticker → always 200 — CONFIRMED (never raises, always returns PCRData)
- Registered via `include_with_api_alias(put_call_ratio_router)` — CONFIRMED in main.py:149-150

**Status: PASS**

### AC-6: Frontend
- `client.ts`: PCRSentiment, ExpiryPCR, PCRData, fetchPutCallRatio — all present at lines 1907-1954
- `PutCallRatioPanel.tsx`: PCR gauge (PCRGauge component), sentiment signal (sentimentColor/sentimentLabel), OI/Volume comparison (4 metric cards), expiry breakdown (ExpiryRow table) — all present
- `RiskReviewCenter.tsx`: imports PutCallRatioPanel at line 29, renders `<PutCallRatioPanel />` at line 53 — CONFIRMED
- TypeScript tsc --noEmit: PASS (no errors)
- Vite build: PASS (built in 396ms)

**Status: PASS**

---

## 7. Summary

All 6 acceptance criteria pass. 28 tests all green. Ruff, mypy, TypeScript, and Vite all clean. File scope exactly matches the whitelist. No cross-app imports. No scope creep.

**VERDICT: PASS**
