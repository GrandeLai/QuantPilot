# Acceptance Report: phaseF15.social-sentiment

**Run at**: 2026-04-29T00:00:00Z
**Implementation PR**: commit 54b62fe
**Diff range**: `HEAD~1..HEAD`
**Acceptance-agent invocation**: claude-sonnet-4-6 (2026-04-29)
**Verdict**: PASS

## 文件影响范围检查

- 改动文件总数：9
- 在白名单内：9
- 超出白名单：0

Changed files vs whitelist:
1. `apps/stock-assistant/backend/src/quantpilot_stock/social_sentiment/__init__.py` — in whitelist
2. `apps/stock-assistant/backend/src/quantpilot_stock/social_sentiment/engine.py` — in whitelist
3. `apps/stock-assistant/backend/src/quantpilot_stock/api/social_sentiment.py` — in whitelist
4. `apps/stock-assistant/backend/src/quantpilot_stock/main.py` — in whitelist
5. `apps/stock-assistant/backend/tests/test_social_sentiment.py` — in whitelist
6. `apps/stock-assistant/frontends/workbench/src/api/client.ts` — in whitelist
7. `apps/stock-assistant/frontends/workbench/src/components/SocialSentimentPanel.tsx` — in whitelist
8. `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx` — in whitelist
9. `docs/tasks/phaseF15/social-sentiment.md` — in whitelist

Note: `docs/acceptance/phaseF15/social-sentiment.md` (this file) is also listed in the spec whitelist.

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: Engine correctness (SentimentGrade, PumpRiskLevel, SocialSentimentData, _sentiment_grade thresholds, _pump_risk_score formula, graceful degradation, httpx 10s timeout) | ✅ PASS | engine.py: SentimentGrade 5-value Literal confirmed (line 30-33); PumpRiskLevel 3-value Literal confirmed (line 34); SocialSentimentData dataclass with all 11 fields confirmed (lines 41-54); _sentiment_grade thresholds match spec exactly (lines 61-71); _pump_risk_score formula matches spec: bullish_extremity = max(0, (ratio-0.5)*2), volume_factor = min(1.0, count/20), score = 0.7*extremity + 0.3*volume_factor (lines 74-87); compute_social_sentiment catches all exceptions, returns degraded result with api_accessible=False (lines 133-209); httpx.Client with timeout=10.0 (lines 37, 159) |
| AC-2: API (GET /api/social-sentiment?ticker=AAPL → 200, missing ticker → 422, registered via include_with_api_alias) | ✅ PASS | api/social_sentiment.py confirmed: router prefix "/social-sentiment", endpoint always returns 200 (never raises, calls engine which never raises). main.py line 128: `include_with_api_alias(social_sentiment_router)` confirmed. Tests confirm 422 on missing ticker (test_missing_ticker_returns_422 PASSED) and 200 always (test_always_returns_200_even_when_api_down PASSED) |
| AC-3: Frontend (SocialSentimentData/SentimentGrade/PumpRiskLevel types + fetchSocialSentiment in client.ts; SocialSentimentPanel with ratio bar + pump_risk indicator + API degradation banner; panel added to RiskReviewCenter.tsx; TypeScript build no errors) | ✅ PASS | client.ts lines 1405-1445: SentimentGrade (5-value union), PumpRiskLevel (3-value union), SocialSentimentData interface (11 fields), fetchSocialSentiment function all present. SocialSentimentPanel.tsx: SentimentBar sub-component (ratio bar, lines 59-152), PumpRiskIndicator sub-component (lines 158-263), API degradation banner when !result.api_accessible (lines 380-394). RiskReviewCenter.tsx: import at line 18, `<SocialSentimentPanel />` at line 31. Frontend build: `✓ built in 719ms` exit code 0 |
| AC-4: Tests (≥16): _sentiment_grade boundaries, _pump_risk_score logic, compute_social_sentiment happy path, API unreachable → api_accessible=False, API 200 + 422 | ✅ PASS | 35 tests collected and all passed in 6.90s. Breakdown: TestSentimentGrade (10 tests), TestPumpRiskScore (7 tests), TestPumpRiskLevel (4 tests), TestComputeSocialSentiment (5 tests), TestGracefulDegradation (6 tests), TestSocialSentimentAPIEndpoint (3 tests). Exceeds ≥16 requirement. |

## 测试执行日志摘要

### `uv run pytest tests/test_social_sentiment.py -v`
- 退出码：0
- 关键输出：
  ```
  collected 35 items
  TestSentimentGrade::test_above_70_is_very_bullish PASSED
  TestSentimentGrade::test_exactly_70_is_bullish PASSED
  ... (all 35 tests) ...
  TestSocialSentimentAPIEndpoint::test_happy_path_returns_200_with_all_fields PASSED
  35 passed in 6.90s
  ```

### `/Users/bytedance/code/QuantPilot/backend/.venv/bin/mypy src/quantpilot_stock/social_sentiment/ src/quantpilot_stock/api/social_sentiment.py`
- 退出码：0
- 关键输出：`Success: no issues found in 3 source files`

### `ruff check src/quantpilot_stock/social_sentiment/ src/quantpilot_stock/api/social_sentiment.py`
- 退出码：0
- 关键输出：`All checks passed!`

### `npm run build --prefix apps/stock-assistant/frontends/workbench`
- 退出码：0
- 关键输出：`✓ built in 719ms`

### `bash common/schemas/codegen.sh && git diff --exit-code`
- 退出码：0
- 关键输出：codegen for 6 schemas completed; no drift detected

## 代码 Review 备注

1. engine.py has a module-level docstring and all functions have full type hints — compliant with CLAUDE.md constraints.
2. __init__.py has a module-level docstring and re-exports the public interface cleanly.
3. api/social_sentiment.py has a module-level docstring. Uses `asyncio.get_event_loop()` (line 79) which is deprecated in Python 3.10+ in favor of `asyncio.get_running_loop()`. This is a minor style concern; it functions correctly in the current test environment (Python 3.12 still allows it in async context). Not a blocking issue.
4. No cross-app imports detected; no `apps/*` imports in `common/`.
5. No out-of-scope refactoring detected.

## 后续动作

- PR可合：无阻塞项。建议在合并后将此任务更新到 docs/acceptance/INDEX.md。
- 可选改进（非阻塞）：将 `asyncio.get_event_loop()` 替换为 `asyncio.get_running_loop()` 以消除 Python 3.12 的 DeprecationWarning。
