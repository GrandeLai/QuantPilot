# Acceptance Report: phaseF2.edgar-fetcher

**Run at**: 2026-04-29T00:00:00Z
**Implementation PR**: untracked working-tree changes (no commit yet)
**Diff range**: `git status` — untracked/modified files against HEAD
**Acceptance-agent invocation**: claude-sonnet-4-6 session 2026-04-29
**Verdict**: FAIL

---

## 文件影响范围检查

White-listed paths (from task spec):

| Type   | Path |
|--------|------|
| NEW    | `apps/stock-assistant/backend/src/quantpilot_stock/edgar/__init__.py` |
| NEW    | `apps/stock-assistant/backend/src/quantpilot_stock/edgar/models.py` |
| NEW    | `apps/stock-assistant/backend/src/quantpilot_stock/edgar/client.py` |
| NEW    | `apps/stock-assistant/backend/tests/test_edgar_client.py` |
| MODIFY | `apps/stock-assistant/backend/pyproject.py` |

Actual changes detected (`git status`):

### Within whitelist (5 files)
- `apps/stock-assistant/backend/src/quantpilot_stock/edgar/__init__.py` — NEW, in whitelist
- `apps/stock-assistant/backend/src/quantpilot_stock/edgar/models.py` — NEW, in whitelist
- `apps/stock-assistant/backend/src/quantpilot_stock/edgar/client.py` — NEW, in whitelist
- `apps/stock-assistant/backend/tests/test_edgar_client.py` — NEW, in whitelist
- `apps/stock-assistant/backend/pyproject.toml` — MODIFIED, in whitelist

### Outside whitelist — FAIL (10 items)

| Path | Type | Reason |
|------|------|--------|
| `apps/stock-assistant/backend/src/quantpilot_stock/edgar/diff_engine.py` | NEW | Not in spec whitelist; implements an 8-K diff engine beyond the defined scope |
| `apps/stock-assistant/backend/src/quantpilot_stock/edgar/form4_engine.py` | NEW | Not in spec whitelist; implements a Form 4 cluster-signal engine beyond the defined scope |
| `apps/stock-assistant/backend/src/quantpilot_stock/api/sec.py` | NEW | Not in spec; REST API layer for edgar module is scope creep |
| `apps/stock-assistant/backend/src/quantpilot_stock/main.py` | MODIFIED | Not in spec; adds `sec_router` registration (consequence of out-of-scope `api/sec.py`) |
| `apps/stock-assistant/backend/tests/test_edgar_diff_engine.py` | NEW | Not in spec; tests for out-of-scope diff_engine |
| `apps/stock-assistant/backend/tests/test_form4_cluster.py` | NEW | Not in spec; tests for out-of-scope form4_engine |
| `apps/stock-assistant/backend/tests/test_sec_api.py` | NEW | Not in spec; tests for out-of-scope api/sec.py |
| `apps/stock-assistant/frontends/workbench/src/api/client.ts` | MODIFIED | Not in spec; adds TypeScript SEC API types and functions |
| `apps/stock-assistant/frontends/workbench/src/components/SECEventsPanel.tsx` | NEW | Not in spec; workbench frontend panel |
| `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx` | MODIFIED | Not in spec |
| `uv.lock` | MODIFIED | Implied by pyproject.toml change — acceptable companion |
| `docs/tasks/phaseF2/` | NEW dir | Contains the task spec — acceptable |

**Total out-of-whitelist files causing FAIL: 10** (excluding uv.lock and docs/tasks/ which are acceptable companions).

Per the acceptance-agent hard constraint: "文件影响范围超出白名单 → FAIL（无论 AC 状态）".

---

## 验收标准核对

| AC | 状态 | 证据 |
|----|------|------|
| AC-1: 模块文件存在 (`__init__.py`, `models.py`, `client.py`) | ✅ PASS | `test -f` all three files returned exit 0 |
| AC-2: 数据模型完整 (EightKFiling, EightKItem, Form4Transaction in models.py) | ✅ PASS | `grep -q "EightKFiling\|EightKItem\|Form4Transaction"` exit 0; all three dataclasses defined with correct fields |
| AC-3: 客户端函数签名 (get_cik, get_recent_8k_filings, get_form4_transactions in client.py) | ✅ PASS | `grep -q` exit 0; all three async functions present with correct signatures |
| AC-4: User-Agent 限速 (QuantPilot / rate_limit / sleep in client.py) | ✅ PASS | `_USER_AGENT = "QuantPilot/1.0 jdawlaia@gmail.com"`, `_RATE_LIMIT_INTERVAL = 0.11`, `_rate_limit()` using `asyncio.sleep` all present |
| AC-5: 单元测试通过 (≥8 tests, httpx mock, exit 0) | ✅ PASS | `pytest tests/test_edgar_client.py -v` — 14 tests collected, 14 passed in 0.52s; exit 0 |
| AC-6: mypy 通过 | ✅ PASS | `uv run --isolated --with mypy python -m mypy src/quantpilot_stock/edgar/` — "Success: no issues found in 5 source files"; exit 0 |

All 6 ACs pass individually. However file scope violation overrides to FAIL.

**Additional gap found**: task spec requires `lxml>=5.0.0` added to `pyproject.toml` alongside `rapidfuzz>=3.0.0`. Only `rapidfuzz>=3.0.0` was added. `lxml` is absent.

---

## 测试执行日志摘要

### `uv run pytest tests/test_edgar_client.py -v`
- 退出码: 0
- 关键输出:
  ```
  collected 14 items
  tests/test_edgar_client.py::TestStripHTML::test_plain_text_unchanged PASSED
  tests/test_edgar_client.py::TestStripHTML::test_removes_tags PASSED
  tests/test_edgar_client.py::TestStripHTML::test_empty_string PASSED
  tests/test_edgar_client.py::TestStripHTML::test_no_html PASSED
  tests/test_edgar_client.py::TestParse8KItems::test_parses_single_item PASSED
  tests/test_edgar_client.py::TestParse8KItems::test_parses_multiple_items PASSED
  tests/test_edgar_client.py::TestParse8KItems::test_empty_text_returns_empty_list PASSED
  tests/test_edgar_client.py::TestParse8KItems::test_no_items_returns_empty_list PASSED
  tests/test_edgar_client.py::TestGetCik::test_known_ticker_returns_cik PASSED
  tests/test_edgar_client.py::TestGetCik::test_case_insensitive PASSED
  tests/test_edgar_client.py::TestGetCik::test_unknown_ticker_raises_on_network_error PASSED
  tests/test_edgar_client.py::TestGetRecent8KFilings::test_returns_list_of_filings PASSED
  tests/test_edgar_client.py::TestGetRecent8KFilings::test_max_count_respected PASSED
  tests/test_edgar_client.py::TestGetForm4Transactions::test_parses_purchase_transaction PASSED
  14 passed in 0.52s
  ```

### `uv run --isolated --with mypy python -m mypy src/quantpilot_stock/edgar/`
- 退出码: 0
- 关键输出: `Success: no issues found in 5 source files`
- Note: mypy checked 5 source files (including `diff_engine.py` and `form4_engine.py` which are out of spec scope but exist in the edgar/ package)

---

## 代码 Review 备注

**Quality observations (non-blocking individually, blocked by scope issue):**

1. `models.py`: Has module-level docstring, full type hints, all fields match spec exactly. Clean.
2. `client.py`: Has module-level docstring, type hints, loguru logger, async-first, rate limiter implemented correctly at 0.11s interval. `_USER_AGENT` matches the spec exactly. Good.
3. `__init__.py`: Has docstring; exports the 3 public types correctly via `__all__`. Clean.
4. `tests/test_edgar_client.py`: 14 tests covering HTML stripping, 8-K item parsing, CIK lookup (known + case-insensitive + unknown-ticker-error), 8-K retrieval (mock), max_count limit, and Form4 purchase parsing. All use httpx mocks — no real network calls.
5. **No cross-app imports**: edgar module only imports from `quantpilot_stock.*` — compliant.
6. **Missing dependency**: `lxml>=5.0.0` is in the spec's pyproject.toml requirement but absent from the actual diff; only `rapidfuzz>=3.0.0` was added.

**Scope creep details:**
- `diff_engine.py` + `form4_engine.py`: These are in a *later* task (edgar-diff-engine, already separately accepted per `docs/acceptance/phaseF2/edgar-diff-engine.md`). Their presence here means the implementation conflated two distinct tasks.
- `api/sec.py` + `main.py` registration + frontend `client.ts` + `SECEventsPanel.tsx` + `RiskReviewCenter.tsx`: Full API + frontend layer was built on top of the fetcher in the same working-tree change. This is well beyond the phaseF2.edgar-fetcher scope.

---

## 后续动作

Verdict is **FAIL** due to 10 files outside the whitelist.

### Required fixes (implementation agent):

1. **Split out scope-creep files**: The edgar-fetcher task should only include:
   - `edgar/__init__.py`, `edgar/models.py`, `edgar/client.py`
   - `tests/test_edgar_client.py`
   - `pyproject.toml` (adding both `rapidfuzz>=3.0.0` AND `lxml>=5.0.0`)
   - `uv.lock` (auto-updated)

2. **Add `lxml>=5.0.0` to pyproject.toml**: The spec explicitly lists it as a required dependency addition; it is currently missing.

3. **Remove or defer out-of-whitelist files** from this task's commit:
   - `edgar/diff_engine.py` — belongs to phaseF2.edgar-diff-engine (already separately accepted)
   - `edgar/form4_engine.py` — belongs to a separate task
   - `api/sec.py`, `main.py` changes — separate task needed
   - `tests/test_edgar_diff_engine.py`, `tests/test_form4_cluster.py`, `tests/test_sec_api.py` — separate tasks
   - `frontends/workbench/src/api/client.ts`, `SECEventsPanel.tsx`, `RiskReviewCenter.tsx` — separate task

4. **Commit message**: Must include `Refs: docs/tasks/phaseF2/edgar-fetcher.md` per CLAUDE.md convention.

If `diff_engine.py` and `form4_engine.py` are legitimately needed as internal helpers for `client.py`, the spec whitelist should be updated to include them and this acceptance re-run.

**Note to user**: The implementation quality for the in-scope portion (edgar module core + tests) is high — all 6 ACs pass once the scope is properly isolated. The fix is organizational (splitting the commit / staging only the whitelisted files) rather than substantive code changes, plus adding `lxml` to pyproject.toml.
