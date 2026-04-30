# Acceptance Report: F.29 — 期权最大痛苦值面板 (Max Pain Calculator)

**Run at**: 2026-04-30T03:00:00Z
**Implementation PR**: commits d7545e6 (feat(F.29)) + d1f6f8c (fix(F.29): align spec to weak_pull)
**Diff range**: `d7545e6^..d1f6f8c`
**Acceptance-agent invocation**: claude-sonnet-4-6, 2026-04-30 (v2 — re-run after spec correction)
**Verdict**: PASS

---

## 文件影响范围检查

The F.29-specific files changed across both commits:

- 改动文件（F.29 scope）：9
- 在白名单内：9
- 超出白名单：0

Files verified in whitelist:
- `apps/stock-assistant/backend/src/quantpilot_stock/max_pain/__init__.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/max_pain/engine.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/api/max_pain.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`
- `apps/stock-assistant/backend/tests/test_max_pain.py`
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`
- `apps/stock-assistant/frontends/workbench/src/components/MaxPainPanel.tsx`
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
- `docs/tasks/phaseF29/max-pain.md`

**Note**: Commit d1f6f8c bundled F.30 files (`technical_score/`, `TechnicalScorePanel.tsx`,
`docs/tasks/phaseF30/technical-score.md`, plus additions to `client.ts` and `RiskReviewCenter.tsx`).
Those additions belong exclusively to task F.30 and are not part of F.29 scope. The F.30 additions
within whitelist-shared files (`client.ts`, `RiskReviewCenter.tsx`) are additive-only and do not
alter any F.29 functionality. This is treated as a bundled commit issue for F.30's own acceptance,
not a F.29 whitelist violation.

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: MaxPainSignal enum + ExpiryMaxPain + MaxPainData dataclasses | ✅ PASS | engine.py:30-36 defines `MaxPainSignal = Literal["pin_zone","bullish_pull","bearish_pull","weak_pull","unknown"]` — matches spec exactly. ExpiryMaxPain (expiry, dte, max_pain_strike, current_price, distance_pct, total_call_oi, total_put_oi, signal) and MaxPainData (ticker, current_price, as_of_date, data_available, interpretation, expiries) both correct. client.ts:1998-2013 mirrors the same types. |
| AC-2: 计算逻辑 (Max Pain argmin, distance_pct, signal classification) | ✅ PASS | engine.py:76-140 implements argmin Σ[call_OI*max(0,K-spot)+put_OI*max(0,spot-K)]. distance_pct=(max_pain-current)/current*100 at line 257. _classify_signal: <2%→pin_zone, 2-5% positive→bullish_pull, 2-5% negative→bearish_pull, ≥5%→weak_pull (engine.py:143-150). Nearest 4 expiries DTE 1-45 enforced. All 28 tests pass including boundary tests at 2.0% and 5.0%. |
| AC-3: 降级策略 | ✅ PASS | engine.py:223-232 returns data_available=True, expiries=[] when no option_dates. engine.py:204-209 returns data_available=False on yfinance exception. Both paths tested and passing. |
| AC-4: ≥16 tests, all mocked, full signal coverage | ✅ PASS | 28 tests collected, 28 passed. TestClassifySignal covers pin_zone (2), bullish_pull (1), bearish_pull (1), weak_pull (2), boundary cases at 2.0% and 5.0%. _compute_max_pain: normal + empty chain + only calls + zero OI + single strike. Integration: data_available, expiry fields, no options, current_price, interpretation, yfinance exception, DTE filter, sort by DTE. API: 422/200/fields/yfinance-fail. All network calls mocked via @patch("quantpilot_stock.max_pain.engine.yf.Ticker"). **Minor**: AC-4 text at line 62 of spec still lists "near_pin" in coverage description (not updated by the fix commit); however the actual tests cover "weak_pull" correctly and the intent is satisfied. |
| AC-5: GET /api/max-pain?ticker=, 422/200, include_with_api_alias | ✅ PASS | test_no_ticker_returns_422 and test_with_ticker_returns_200 both pass. main.py registers via include_with_api_alias(max_pain_router). |
| AC-6: client.ts types + MaxPainPanel.tsx + RiskReviewCenter + TS/Vite build | ✅ PASS | client.ts:1998-2039 defines MaxPainSignal/ExpiryMaxPain/MaxPainData/fetchMaxPain. MaxPainPanel.tsx has ticker input, analyze button, ExpiryRow (DTE/MaxPain/distance/signal), PriceVsMaxPainBar visualization, signal badges (pin_zone amber #f59e0b, bullish_pull green #00C087, bearish_pull red #ef4444, weak_pull slate). RiskReviewCenter.tsx imports and renders <MaxPainPanel />. Vite build: exit 0, 528ms, tsc -b clean. |

---

## 测试执行日志摘要

### `uv run pytest tests/test_max_pain.py -v`
- 退出码：0
- 关键输出：28 passed in 5.66s
- 覆盖：TestComputeMaxPain(5) + TestClassifySignal(8) + TestGetDte(3) + TestComputeMaxPainIntegration(8) + TestMaxPainAPI(4)

### `uv run ruff check src/quantpilot_stock/max_pain/ src/quantpilot_stock/api/max_pain.py tests/test_max_pain.py`
- 退出码：0
- 关键输出：`All checks passed!`

### `uv run mypy src/quantpilot_stock/max_pain/ src/quantpilot_stock/api/max_pain.py`
- 退出码：0
- 关键输出：`Success: no issues found in 3 source files`

### `npm run build` (workbench)
- 退出码：0
- 关键输出：`tsc -b && vite build`; built in 528ms; no TypeScript errors

---

## 代码 Review 备注

1. **模块级 docstring**: engine.py has full module docstring; api/max_pain.py has module docstring; `__init__.py` is a package marker (empty, acceptable).
2. **Type hints**: Comprehensive throughout; Pydantic/dataclass combination correct; mypy clean.
3. **跨 app import**: None. All imports are within quantpilot_stock.
4. **common/ 反向 import**: None.
5. **算法注释**: The comment "Max Pain = 使总损失最大（买方）/ 使 Maker 损失最小的 spot" in engine.py is slightly misleading on direction (argmin minimizes total buyer loss = maximizes buyer pain), but semantically equivalent.
6. **AC-4 spec inconsistency**: Line 62 of the updated spec still says "near_pin" in the test coverage list. This is a residual copy-paste miss from the fix commit. It does not affect implementation correctness — the tests correctly cover "weak_pull". Recommend the spec author update AC-4 coverage list to read "weak_pull" in a follow-up edit.

---

## 後續動作

PASS — no required actions.

Optional: Update docs/tasks/phaseF29/max-pain.md AC-4 line 62 to replace "near_pin" with "weak_pull" for spec consistency. This is cosmetic only and does not affect the PASS verdict.
