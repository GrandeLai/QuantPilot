# Acceptance Report — F.21 Form 4 内部人交易聚类信号

**Task ID**: phaseF21/insider-trading  
**Task Spec**: docs/tasks/phaseF21/insider-trading.md  
**PR Commit**: HEAD (83f2178)  
**Acceptance Date**: 2026-04-30  
**Verdict**: PASS

---

## 1. File Scope Check

PR diff files (`git diff --name-only HEAD~1 HEAD`):

```
apps/stock-assistant/backend/src/quantpilot_stock/api/insider_trading.py
apps/stock-assistant/backend/src/quantpilot_stock/insider_trading/__init__.py
apps/stock-assistant/backend/src/quantpilot_stock/insider_trading/engine.py
apps/stock-assistant/backend/src/quantpilot_stock/main.py
apps/stock-assistant/backend/tests/test_insider_trading.py
apps/stock-assistant/frontends/workbench/src/api/client.ts
apps/stock-assistant/frontends/workbench/src/components/InsiderTradingPanel.tsx
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx
docs/tasks/phaseF21/insider-trading.md
```

All 9 files are within the task spec whitelist. No out-of-scope changes detected.

**Result**: PASS

---

## 2. Static Checks

### ruff

```
uv run ruff check src/quantpilot_stock/insider_trading/ \
  src/quantpilot_stock/api/insider_trading.py \
  tests/test_insider_trading.py
```

Output: `All checks passed!` (exit 0)

**Result**: PASS

### mypy

```
uv run mypy src/quantpilot_stock/insider_trading/ \
  src/quantpilot_stock/api/insider_trading.py
```

Output: `Success: no issues found in 3 source files` (exit 0)

**Result**: PASS

---

## 3. Test Suite

```
uv run pytest tests/test_insider_trading.py -v
```

**30 tests collected, 30 passed** in 7.87s (exit 0).

Test breakdown:
- TestComputeSignal (8 tests): all signal branches covered — cluster_buy, cluster_sell, mixed, no_data, neutral, zero-shares, exactly-2-buyers, 3-sellers
- TestBuildInterpretation (5 tests): all 5 signal types produce correct interpretation text
- TestComputeInsiderTrading (9 tests): cluster_buy, ticker uppercase, as_of_date=today, 10b5-1 excluded, old txns excluded, cluster_sell, no filings → no_data, CIK not found → data_available=False, transactions capped at 20
- TestGracefulDegradation (4 tests): exception → data_available=False, never raises, degraded has today date, EDGAR fetch failure → degraded
- TestInsiderTradingAPIEndpoint (4 tests): missing ticker → 422, always 200 when degraded, happy-path all fields, transactions serialized

**Result**: PASS (30 >= 30 required)

---

## 4. AC Verification

### AC-1 数据模型 ✅ PASS

- `InsiderSignal = Literal["cluster_buy","cluster_sell","mixed","neutral","no_data"]` — present in engine.py line 29
- `InsiderTransaction` dataclass with all required fields (insider_name, title, transaction_date, shares, price_per_share, transaction_type, is_10b5_plan, form_url) — lines 33-42
- `InsiderTradingData` dataclass with all required fields (ticker, cik, signal, cluster_buy_count, cluster_sell_count, net_shares_90d, transactions, interpretation, as_of_date, data_available) — lines 45-55
- Module has docstring; all functions have type hints

### AC-2 信号逻辑 ✅ PASS

- `_CLUSTER_THRESHOLD = 2` (engine.py line 215)
- `_compute_signal`: cluster_buy if buy_count >= 2 and sell_count == 0; cluster_sell if sell_count >= 2 and buy_count == 0; mixed if both >= 2; no_data if both == 0; else neutral — lines 219-235
- Distinct insider counting: `sum(1 for s in buys.values() if s > 0)` — correct by-name aggregation

### AC-3 数据过滤 ✅ PASS

- 90-day cutoff: `cutoff = date.today() - timedelta(days=_WINDOW_DAYS)` (engine.py line 279); transactions where `t["transaction_date"] < cutoff` are skipped (line 325)
- 10b5-1 excluded: `if t["is_10b5_plan"]: continue` (line 322)
- Only P/S types: `if t["transaction_type"] not in ("P", "S"): continue` (line 327)

### AC-4 测试要求 ✅ PASS

- 30 tests collected and passed (>= 16 required, >= 30 target)
- All branches of `_compute_signal` covered (TestComputeSignal, 8 tests)
- All branches of `_build_interpretation` covered (TestBuildInterpretation, 5 tests)
- 10b5-1 exclusion: `test_10b5_plan_txn_excluded` PASSED
- 90-day exclusion: `test_old_transactions_excluded` PASSED
- CIK not found → data_available=False: `test_cik_not_found_gives_degraded` PASSED
- EDGAR exception → data_available=False: `test_exception_gives_data_available_false` + `test_edgar_fetch_failure_gives_degraded` PASSED
- Transaction cap at 20: `test_transactions_limited_to_20` PASSED
- All tests mock EDGAR functions; no real network calls

### AC-5 API ✅ PASS

- Route: `GET /api/insider-trading?ticker=<TICKER>` (prefix="/insider-trading" on router; API alias applied via include_with_api_alias)
- Missing ticker → HTTP 422: `test_missing_ticker_returns_422` PASSED (Query(...) with no default)
- Always HTTP 200: `test_always_200_even_when_degraded` PASSED
- Registration in main.py line 139-140: `from quantpilot_stock.api.insider_trading import router as insider_trading_router` + `include_with_api_alias(insider_trading_router)` — confirmed present

### AC-6 前端 ✅ PASS

- **client.ts**: InsiderSignal type (line 1673), InsiderTransactionItem interface (line 1680), InsiderTradingData interface (line 1691), fetchInsiderTrading function (line 1704) — all present
- **InsiderTradingPanel.tsx**:
  - Signal badge with color coding: `signalColor()` + `signalLabel()` render colored span (lines 25-42, 251-263)
  - Buy/sell insider count cards: cluster_buy_count and cluster_sell_count displayed in styled divs (lines 284-303)
  - Net shares change: `result.net_shares_90d` formatted via `fmtShares()` (line 265)
  - Last 10 transactions table: `result.transactions.slice(0, 10).map(...)` with TxnRow (lines 355-366)
  - Degradation banner: `!result.data_available` warning block (lines 217-231)
- **RiskReviewCenter.tsx**: `import InsiderTradingPanel from "../InsiderTradingPanel"` (line 24) + `<InsiderTradingPanel />` rendered (line 43) — confirmed present
- **Vite build**: exit 0, `built in 1.43s`, no TypeScript/build errors

---

## 5. Code Review Notes

- All Python files have module-level docstrings and type hints — compliant with CLAUDE.md
- No cross-app imports; engine.py only uses stdlib + no apps/* imports
- No out-of-scope refactoring detected
- `_parse_form4_xml` uses regex-based XML parsing (no xml.etree dep) — practical for SEC HTML/XML variability
- `_TICKER_CIK_CACHE` is a module-level dict used as a process-level cache; appropriate for this use case
- Exception handling with `# noqa: BLE001` is consistent with other engines in the codebase

---

## 6. Summary

| Check | Result |
|---|---|
| File scope | PASS |
| ruff | PASS |
| mypy | PASS |
| pytest (30/30) | PASS |
| AC-1 data models | PASS |
| AC-2 signal logic | PASS |
| AC-3 data filtering | PASS |
| AC-4 test coverage | PASS |
| AC-5 API registration | PASS |
| AC-6 frontend | PASS |

**Overall Verdict: PASS**
