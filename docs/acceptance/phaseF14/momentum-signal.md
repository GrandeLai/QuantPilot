# Acceptance Report: phaseF14.momentum-signal

**Run at**: 2026-04-29T00:00:00Z
**Implementation PR**: commit 221997a (feat(F.14): Price Momentum Signal — Jegadeesh-Titman factor)
**Diff range**: `da65d9e..221997a`
**Acceptance-agent invocation**: claude-sonnet-4-6 session, 2026-04-29
**Verdict**: PASS

---

## 文件影响范围检查

- 改动文件总数：9
- 在白名单内：9
- 超出白名单：0

Changed files vs whitelist:

| File | In whitelist? |
|---|---|
| `apps/stock-assistant/backend/src/quantpilot_stock/api/momentum.py` | Yes |
| `apps/stock-assistant/backend/src/quantpilot_stock/main.py` | Yes |
| `apps/stock-assistant/backend/src/quantpilot_stock/momentum/__init__.py` | Yes |
| `apps/stock-assistant/backend/src/quantpilot_stock/momentum/engine.py` | Yes |
| `apps/stock-assistant/backend/tests/test_momentum.py` | Yes |
| `apps/stock-assistant/frontends/workbench/src/api/client.ts` | Yes |
| `apps/stock-assistant/frontends/workbench/src/components/MomentumPanel.tsx` | Yes |
| `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx` | Yes |
| `docs/tasks/phaseF14/momentum-signal.md` | Yes |

No scope creep detected.

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: engine.py — MomentumGrade Literal, MomentumSignal dataclass, _momentum_grade, compute_momentum_signal, yfinance 13mo, 12-1m, 52w rolling, proximity | PASS | Read engine.py: all types/dataclass/functions present. MomentumGrade Literal with 5 values. Dataclass has all 12 required fields. _momentum_grade thresholds match spec exactly (>20, >5, >=-5, >=-20). yfinance period="13mo". 52w via rolling 252-bar window. proximity = current/high. |
| AC-2: API — GET /api/momentum?ticker=AAPL 200, no data 404, missing ticker 422, include_with_api_alias | PASS | api/momentum.py: router prefix="/momentum". 404 on None result. 422 automatic via FastAPI Query(...). main.py line 125-126: include_with_api_alias(momentum_router). Tests test_returns_200, test_returns_404_when_no_data, test_missing_ticker_returns_422 all passed. |
| AC-3: frontend — MomentumSignalData, MomentumGrade in client.ts, fetchMomentumSignal, MomentumPanel.tsx shows all data, added to RiskReviewCenter | PASS | client.ts lines 1361-1399: MomentumGrade type, MomentumSignalData interface, fetchMomentumSignal function all present. MomentumPanel.tsx displays 12-1m/1m/3m/6m returns, PositionGauge (52w high/low), grade badge, interpretation. RiskReviewCenter.tsx line 17: import MomentumPanel, line 29: <MomentumPanel />. |
| AC-4: tests >= 18, grade boundaries, happy path, insufficient data None, exception None, API 200/404/422 | PASS | 31 tests collected and passed. 13 grade boundary tests in TestMomentumGrade. Happy path in TestComputeMomentumSignal (rising/falling prices, proximity, returns). test_returns_none_on_insufficient_data, test_returns_none_on_empty_history, test_returns_none_on_exception all pass. API 200/404/422 tested. |

---

## 测试执行日志摘要

### `uv run pytest tests/test_momentum.py -v`
- Exit code: 0
- Result: 31 passed in 5.82s
- All test classes: TestMomentumGrade (13), TestComputeMomentumSignal (12), TestMomentumAPIEndpoint (6)

### `uv run --with mypy mypy src/quantpilot_stock/momentum/engine.py src/quantpilot_stock/api/momentum.py --ignore-missing-imports`
- Exit code: 0
- Output: "Success: no issues found in 2 source files"

### `/opt/homebrew/bin/node .../tsc --noEmit --project apps/stock-assistant/frontends/workbench/tsconfig.json`
- Exit code: 0
- Output: (no output = clean build)

---

## 代码 Review 备注

- engine.py has module-level docstring (citing Jegadeesh & Titman 1993, empirical data) — good.
- All functions have type hints. `_momentum_grade(momentum_12_1_pct: float) -> MomentumGrade` is correctly typed.
- No cross-app imports detected. Only intra-app `quantpilot_stock.*` imports used.
- The `compute_momentum_signal` fallback to `return_6m` when bars_12m+1 > n is a reasonable defensive measure for tickers with < 252 bars; this is explicitly noted in the code comment.
- `_interpretation` uses a dict lookup so any MomentumGrade value missing from the dict would cause a KeyError at runtime; however, all 5 grades are present, so this is safe.
- Minor: `bars_12m = min(252, n-1)` means with exactly 60 bars, `price_12m_ago` will fall back to `return_6m`; this is acceptable given the data constraint check is >= 60 bars.
- No issues found that would affect correctness or spec compliance.

---

## 后续动作

PASS — PR is ready to merge. No outstanding prerequisites.
