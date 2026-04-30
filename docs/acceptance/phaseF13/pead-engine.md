# Acceptance Report: phaseF13.pead-engine

**Run at**: 2026-04-29T16:00:00Z
**Implementation PR**: commit da65d9e27a9450d7c9b493ae579946f7da6aa4ad
**Diff range**: `HEAD~1..HEAD`
**Acceptance-agent invocation**: claude-sonnet-4-6 session (2026-04-29)
**Verdict**: PASS

## 文件影响范围检查

- 改动文件总数：9
- 在白名单内：9
- 超出白名单：0

改动文件清单（全部在白名单内）：
- `apps/stock-assistant/backend/src/quantpilot_stock/api/pead.py` ✓
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py` ✓
- `apps/stock-assistant/backend/src/quantpilot_stock/pead/__init__.py` ✓
- `apps/stock-assistant/backend/src/quantpilot_stock/pead/engine.py` ✓
- `apps/stock-assistant/backend/tests/test_pead.py` ✓
- `apps/stock-assistant/frontends/workbench/src/api/client.ts` ✓
- `apps/stock-assistant/frontends/workbench/src/components/PEADPanel.tsx` ✓
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx` ✓
- `docs/tasks/phaseF13/pead-engine.md` ✓

Note: `docs/acceptance/phaseF13/pead-engine.md` is written by the acceptance agent and is listed in the whitelist.

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1 引擎（pead/engine.py）：EarningsSurpriseGrade Literal, EarningsEvent dataclass, PEADSignal dataclass, _surprise_grade thresholds, PEAD_DRIFT dict, compute_pead_signal returns None on no data/exception | ✅ PASS | All dataclasses, Literal, PEAD_DRIFT dict, and _surprise_grade verified by code review; 33 pytest tests pass covering all branches |
| AC-2 API（api/pead.py）：GET /api/pead?ticker=AAPL 200, no data 404, missing ticker 422, router via include_with_api_alias | ✅ PASS | test_returns_200, test_returns_404_when_no_data, test_missing_ticker_returns_422 all pass; grep confirms `include_with_api_alias(pead_router)` in main.py |
| AC-3 前端（PEADPanel.tsx + client.ts）：types, fetchPEADSignal, PEADPanel component, RiskReviewCenter import, TS build clean | ✅ PASS | EarningsEventData, PEADSignalData, EarningsSurpriseGrade, fetchPEADSignal confirmed in client.ts (lines 1313-1352); PEADPanel.tsx exists (440 lines); RiskReviewCenter.tsx imports PEADPanel (line 16) and renders it (line 27); tsc --noEmit exits 0 |
| AC-4 测试（≥ 18 个）：_surprise_grade boundary tests, compute_pead_signal happy/sad paths, API 200/404/422 | ✅ PASS | 33 tests collected and passed (exit code 0); covers all grades + boundaries, empty DataFrame → None, exception → None, API 200/404/422 |

## 测试执行日志摘要

### `uv run pytest tests/test_pead.py -v`
- 退出码：0
- 关键输出：
  ```
  collected 33 items
  tests/test_pead.py::TestSurpriseGrade::test_large_beat PASSED
  tests/test_pead.py::TestSurpriseGrade::test_beat PASSED
  tests/test_pead.py::TestSurpriseGrade::test_boundary_large_beat PASSED  [exactly +10 = beat, not large_beat]
  tests/test_pead.py::TestSurpriseGrade::test_negative_two_is_miss PASSED  [exactly -2 = miss, not inline]
  tests/test_pead.py::TestComputePEADSignal::test_returns_none_on_empty_earnings_dates PASSED
  tests/test_pead.py::TestComputePEADSignal::test_returns_none_on_exception PASSED
  tests/test_pead.py::TestPEADAPIEndpoint::test_returns_200 PASSED
  tests/test_pead.py::TestPEADAPIEndpoint::test_returns_404_when_no_data PASSED
  tests/test_pead.py::TestPEADAPIEndpoint::test_missing_ticker_returns_422 PASSED
  ... (33 total)
  33 passed in 5.78s
  ```

### `uv run --with mypy mypy src/quantpilot_stock/pead/engine.py src/quantpilot_stock/api/pead.py --ignore-missing-imports`
- 退出码：0
- 关键输出：`Success: no issues found in 2 source files`

### `tsc --noEmit --project apps/stock-assistant/frontends/workbench/tsconfig.json`
- 退出码：0
- 关键输出：(no output = clean)

## 代码 Review 备注

- engine.py has module-level docstring and full type hints — CLAUDE.md constraint satisfied.
- api/pead.py has module-level docstring and type hints — satisfied.
- No cross-app imports found in pead/ module.
- PEAD_DRIFT values match spec exactly: large_beat (3.5, 5.2, 6.8), beat (1.8, 2.8, 3.5), inline (0.0, 0.0, 0.0), miss (-1.8, -2.8, -3.5), large_miss (-3.5, -5.2, -6.8).
- _surprise_grade thresholds confirmed correct: >10 = large_beat (strictly greater, so 10.0 → beat), ≥2 = beat, >-2 = inline, ≥-10 = miss, <-10 = large_miss. The boundary at -2.0 (miss, not inline) is correctly implemented and tested.
- compute_pead_signal is wrapped in a broad try/except → never raises, returns None on any exception.
- Router registration confirmed in main.py via include_with_api_alias.
- PEADPanel.tsx (440 lines) renders surprise % + grade badge + 30/60/90d drift bars + next earnings date — spec requirements met.
- Minor: `asyncio.get_event_loop()` in api/pead.py is slightly deprecated in favour of `asyncio.get_running_loop()` in async context, but this is a non-blocking advisory only — does not affect correctness or tests.

## 后续动作

PASS — PR can be merged. No blocking issues found.

- Recommended: update `docs/acceptance/INDEX.md` to add this entry.
- Advisory (non-blocking): consider replacing `asyncio.get_event_loop()` with `asyncio.get_running_loop()` in a follow-up cleanup task.
