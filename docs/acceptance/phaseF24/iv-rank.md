# Acceptance Report: F.24 — IV Rank & Volatility Monitor

**Run at**: 2026-04-30T00:00:00Z
**Implementation PR**: commit HEAD (b69856f baseline; iv-rank files in latest commit)
**Diff range**: `HEAD~1..HEAD`
**Acceptance-agent invocation**: claude-sonnet-4-6 session 2026-04-30
**Verdict**: PASS

## 文件影响范围检查

- 改动文件总数：9
- 在白名单内：9
- 超出白名单：0

Changed files (all within whitelist):
- `apps/stock-assistant/backend/src/quantpilot_stock/api/iv_rank.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/iv_rank/__init__.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/iv_rank/engine.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`
- `apps/stock-assistant/backend/tests/test_iv_rank.py`
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`
- `apps/stock-assistant/frontends/workbench/src/components/IVRankPanel.tsx`
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
- `docs/tasks/phaseF24/iv-rank.md`

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 数据模型（IVSignal, TermStructurePoint, IVRankData） | ✅ PASS | engine.py L27 defines `IVSignal = Literal["buy_options","sell_options","neutral","no_data"]`; TermStructurePoint dataclass at L41 with expiry/days_to_expiry/atm_iv; IVRankData dataclass at L48 with all 13 required fields. client.ts mirrors all types at L1816-1843. |
| AC-2: 计算逻辑（HV、IV Rank [0,100]、IV Percentile、ATM IV、Skew、信号） | ✅ PASS | `_compute_hv` uses log-return rolling std × √252 (L69-73). HV30 series used as IV proxy (L276). IV Rank formula at L289 clamped via `max(0.0, min(100.0, raw_rank))` (L290). IV Percentile computed as fraction below current (L292-293). ATM IV is call/put average at nearest strike (L101-102). Put/Call Skew = put_iv − call_iv × 100 (L269). Signal thresholds: <20 → buy_options, >80 → sell_options (L297-304). All verified against test_iv_rank.py::TestIVSignal::test_iv_rank_clamped_0_100 PASSED. |
| AC-3: 期权期限结构（最多5个到期日，DTE≥5，ATM IV，按DTE升序） | ✅ PASS | `_MAX_EXPIRIES=5` (L33), `_MIN_DTE=5` (L32). Loop skips DTE < 5 (L244). term_structure built in expiry order (L253-265). test_iv_rank.py::TestComputeIvRankNormal::test_term_structure_populated PASSED. |
| AC-4: 测试要求（≥16 tests，覆盖_compute_hv边界/ATM IV边界/compute_iv_rank/信号/异常/API） | ✅ PASS | 26 tests collected and passed. Covers: _compute_hv normal+window_before_full+annualisation+volatile (4); _get_atm_iv both/only_calls/only_puts/empty/zero_iv (5); compute_iv_rank normal+term_structure+skew+no_options_fallback (4); signals buy/sell/neutral/clamped (4); graceful degradation yfinance_exception/empty_history/insufficient_history/option_chain_error/uppercase/interpretation (6); API 200/422/network_failure (3). All mock network. |
| AC-5: API（GET /api/iv-rank?ticker=, 无ticker→422，有ticker→200，include_with_api_alias注册） | ✅ PASS | api/iv_rank.py L10: `Query(...)` makes ticker required → 422 on missing. Function always returns IVRankData (never raises). main.py L145-146: `from quantpilot_stock.api.iv_rank import router as iv_rank_router` + `include_with_api_alias(iv_rank_router)`. API tests confirm 200 and 422 behaviors. |
| AC-6: 前端（client.ts types+fetch, IVRankPanel仪表盘+HV+期限结构+信号, RiskReviewCenter集成, tsc+Vite） | ✅ PASS | client.ts exports IVSignal/TermStructurePoint/IVRankData/fetchIVRank at L1816-1857. IVRankPanel.tsx renders IVRankGauge (rank dial), HV comparison, TermStructureTable, and signal badge (signalLabel/signalColor). RiskReviewCenter.tsx imports IVRankPanel at L27 and renders `<IVRankPanel />` at L49. `tsc --noEmit` exits 0 (no output). `vite build` exits 0, built in 342ms. |

## 测试执行日志摘要

### `uv run pytest tests/test_iv_rank.py -v`
- 退出码：0
- 关键输出：26 collected, 26 passed in 5.73s
- All test classes: TestComputeHv (4), TestGetAtmIv (5), TestComputeIvRankNormal (4), TestIVSignal (4), TestGracefulDegradation (6), TestIVRankAPIEndpoint (3)

### `uv run ruff check src/quantpilot_stock/iv_rank/ src/quantpilot_stock/api/iv_rank.py tests/test_iv_rank.py`
- 退出码：0
- 关键输出：All checks passed!

### `uv run mypy src/quantpilot_stock/iv_rank/ src/quantpilot_stock/api/iv_rank.py`
- 退出码：0
- 关键输出：Success: no issues found in 3 source files

### `npx tsc --noEmit`
- 退出码：0
- 关键输出：(no output — no errors)

### `npx vite build`
- 退出码：0
- 关键输出：built in 342ms (no errors or warnings)

## 代码 Review 备注

- engine.py has module-level docstring and type hints throughout — compliant with CLAUDE.md requirements.
- No cross-app imports detected; iv_rank package is self-contained within stock-assistant.
- `__init__.py` is minimal (one comment line) — not a concern since the package is accessed via engine.py directly.
- `_safe_float` helper is a clean defensive utility with proper type ignore annotation.
- The HV30-as-IV-proxy approach is well-documented in comments and spec; acceptable for free-data tier.
- No out-of-scope changes detected (no "bonus refactoring").

## 后续动作

PASS — PR 可合入。No prerequisites beyond standard merge.
