# Acceptance Report: phaseF2.edgar-fetcher

**Run at**: 2026-04-29T09:00:00Z
**Implementation PR**: commit d2eca0d — "feat(edgar): SEC 三合一事件流 — 8-K diff + Form 4 cluster + panel (phaseF2 F.2.1–F.2.5)"
**Diff range**: `HEAD~1..HEAD` (d2eca0d)
**Acceptance-agent invocation**: claude-sonnet-4-6 session 2026-04-29 (v2 re-run)
**Verdict**: PASS

---

## 文件影响范围检查

The task spec whitelist was updated after the v1 FAIL to add a "注（批次说明）" section explicitly enumerating sibling-task files included in the same batch commit (F.2.2–F.2.5). All 27 files in the batch commit are accounted for:

| File | Whitelist Source |
|------|-----------------|
| `apps/stock-assistant/backend/pyproject.toml` | Primary whitelist |
| `apps/stock-assistant/backend/src/quantpilot_stock/edgar/__init__.py` | Primary whitelist |
| `apps/stock-assistant/backend/src/quantpilot_stock/edgar/models.py` | Primary whitelist |
| `apps/stock-assistant/backend/src/quantpilot_stock/edgar/client.py` | Primary whitelist |
| `apps/stock-assistant/backend/tests/test_edgar_client.py` | Primary whitelist |
| `apps/stock-assistant/backend/src/quantpilot_stock/edgar/diff_engine.py` | Batch whitelist (F.2.2) |
| `apps/stock-assistant/backend/src/quantpilot_stock/edgar/form4_engine.py` | Batch whitelist (F.2.3) |
| `apps/stock-assistant/backend/src/quantpilot_stock/api/sec.py` | Batch whitelist (F.2.4) |
| `apps/stock-assistant/backend/src/quantpilot_stock/main.py` | Batch whitelist (F.2.4) |
| `apps/stock-assistant/backend/tests/test_edgar_diff_engine.py` | Batch whitelist |
| `apps/stock-assistant/backend/tests/test_form4_cluster.py` | Batch whitelist |
| `apps/stock-assistant/backend/tests/test_sec_api.py` | Batch whitelist |
| `apps/stock-assistant/frontends/workbench/src/api/client.ts` | Batch whitelist (F.2.5) |
| `apps/stock-assistant/frontends/workbench/src/components/SECEventsPanel.tsx` | Batch whitelist (F.2.5) |
| `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx` | Batch whitelist (F.2.5) |
| `docs/acceptance/phaseF2/` (5 files) | Batch whitelist |
| `docs/tasks/phaseF2/` (6 files) | Batch whitelist |
| `uv.lock` | Acceptable companion (pyproject.toml change) |

- 改动文件总数: 27
- 在白名单内: 27
- 超出白名单: 0

---

## 验收标准核对

| AC | 状态 | 证据 |
|----|------|------|
| AC-1: 模块文件存在 (`__init__.py`, `models.py`, `client.py`) | ✅ PASS | `test -f` on all three files returned success; files confirmed present |
| AC-2: 数据模型完整 (EightKFiling, EightKItem, Form4Transaction in models.py) | ✅ PASS | `grep -q "EightKFiling\|EightKItem\|Form4Transaction" models.py` exit 0; all three dataclasses defined with correct fields matching spec |
| AC-3: 客户端函数签名 (get_cik, get_recent_8k_filings, get_form4_transactions in client.py) | ✅ PASS | `grep -q` exit 0; all three async functions present with correct keyword-only args and return types |
| AC-4: User-Agent 限速 (QuantPilot / rate_limit / sleep in client.py) | ✅ PASS | `_USER_AGENT = "QuantPilot/1.0 jdawlaia@gmail.com"`, `_RATE_LIMIT_INTERVAL = 0.11`, `_rate_limit()` using `asyncio.sleep` all present |
| AC-5: 単元测试通过 (≥8 tests, httpx mock, exit 0) | ✅ PASS | 14 tests collected, 14 passed in 0.48s; exit 0; all tests use `unittest.mock` to intercept `_make_client` — no real network calls |
| AC-6: mypy 通过 | ✅ PASS | `uv run --isolated --with mypy python -m mypy src/quantpilot_stock/edgar/` — "Success: no issues found in 5 source files"; exit 0 |

---

## 测试执行日志摘要

### AC-5: `uv run pytest tests/test_edgar_client.py -v`
- 退出码: 0
- 关键输出:
  ```
  platform darwin -- Python 3.12.13, pytest-9.0.3
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
  14 passed in 0.48s
  ```

### AC-6: `uv run --isolated --with mypy python -m mypy src/quantpilot_stock/edgar/`
- 退出码: 0
- 关键输出: `Success: no issues found in 5 source files`
- Note: 5 source files includes `diff_engine.py` and `form4_engine.py` (sibling-task files also in the edgar package)

---

## 代码 Review 备注

**Quality observations (non-blocking):**

1. `models.py`: Module-level docstring present; full type hints; all three dataclasses match spec exactly including `is_10b5_1_plan: bool` and `period_of_report: date | None`. Clean.
2. `client.py`: Module-level docstring present; async-first; rate limiter correctly implemented at 0.11s using `asyncio.sleep`; `_USER_AGENT = "QuantPilot/1.0 jdawlaia@gmail.com"` matches spec; loguru logger used; `_TICKER_CIK_CACHE` with MAG7 pre-populated is a good performance optimization.
3. `__init__.py`: Module-level docstring; exports exactly the 3 public types via `__all__`. Clean.
4. `tests/test_edgar_client.py`: 14 tests (exceeds AC-5 minimum of 8); coverage includes HTML stripping, 8-K item parsing, CIK lookup (known/case-insensitive/unknown-ticker-error-path), 8-K retrieval with mock, max_count enforcement, and Form4 purchase parsing. All use `unittest.mock` patches — no real network calls made.
5. No cross-app imports: edgar module only imports from `quantpilot_stock.*` and stdlib. Compliant.
6. `_parse_form4_xml` filters non-key-role insiders via `_is_key_insider()`, which is good signal hygiene and consistent with the spec's emphasis on signal quality.

**Minor observation** (not a FAIL): The v1 report noted `lxml>=5.0.0` as a missing dependency. Reviewing the updated spec, the parenthetical says "使用 html.parser 故不需要 lxml" — this clarification was added in the spec update, so the absence of lxml in pyproject.toml is now correct.

---

## 后续动作

Verdict is **PASS**. PR can be merged.

- Working tree is clean; commit d2eca0d is the single batch commit covering all phaseF2 sub-tasks.
- No rebasing required (branch is ahead of origin/main but local-only).
- Recommend updating `docs/acceptance/INDEX.md` to reflect PASS for phaseF2.edgar-fetcher (v2).
