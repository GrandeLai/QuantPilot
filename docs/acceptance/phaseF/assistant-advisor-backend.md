# Acceptance Report: phaseF.assistant-advisor-backend

**Run at**: 2026-04-29T00:00:00+00:00
**Implementation PR**: untracked working tree (new files) + modified main.py
**Diff range**: `git diff main --name-only` (modified) + untracked new files
**Acceptance-agent invocation**: claude-sonnet-4-6, 2026-04-29
**Verdict**: PASS

---

## 文件影响范围检查

- 改动文件（已提交/跟踪，相对 main）：1
  - `apps/stock-assistant/backend/src/quantpilot_stock/main.py` — 在白名单内
- 新增未追踪文件：5
  - `apps/stock-assistant/backend/src/quantpilot_stock/api/advisor.py` — 在白名单内（spec 明确新建）
  - `apps/stock-assistant/backend/src/quantpilot_stock/api/crypto_research.py` — 在白名单内
  - `apps/stock-assistant/backend/tests/test_advisor.py` — 在白名单内
  - `apps/stock-assistant/backend/tests/test_crypto_research.py` — 在白名单内
  - `docs/tasks/phaseF/assistant-advisor-backend.md` — 在白名单内
- 超出白名单：0
- 结论：范围检查通过，无越界改动。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 路由存在（不 404）— `grep -q "advisor"` advisor.py 和 `grep -q "crypto_research\|crypto/research"` crypto_research.py | ✅ PASS | 两个 grep 均命中，router 对象含 prefix `/advisor` 和 `/crypto/research`，所有 6 条路由均已定义 |
| AC-2: advisor + crypto_research 已注册进 main.py — grep advisor_router / crypto_research_router | ✅ PASS | main.py line 64-68 import 两个 router；line 99-100 `include_with_api_alias` 注册，含 `/api` 前缀双挂 |
| AC-3: overview 返回正确 schema（net_worth / cash_ratio / generated_at） | ✅ PASS | advisor.py `/overview` 端点明确返回 `net_worth`, `cash_ratio`, `positions`, `generated_at` 四字段；测试 `test_returns_200_and_schema` 断言全部字段 PASS |
| AC-4: opportunities/risks 使用 funding 信号（引用 analytics） | ✅ PASS | advisor.py 导入并调用 `funding_extreme_signal`, `fetch_binance_funding_history`, `fetch_okx_funding_history` |
| AC-5: crypto_research 返回 market_regime / recommended_strategy_ids | ✅ PASS | crypto_research.py 同时包含 `market_regime` 和 `recommended_strategy_ids` 字段，`/latest` 端点均返回这两个键 |
| AC-6: 测试通过（pytest 退出码 0） | ✅ PASS | 33 passed in 6.16s；test_advisor.py 14 项 + test_crypto_research.py 19 项全绿 |
| AC-7: type-check 通过（mypy 退出码 0） | ✅ PASS | `uv run --isolated --with mypy python -m mypy src/` — "Success: no issues found in 87 source files" |
| AC-8: 不动 workbench / quant-assistant / common | ✅ PASS | `git diff main --name-only -- apps/stock-assistant/frontends/workbench/ apps/quant-assistant/ common/` 输出为空 |

---

## 测试执行日志摘要

### `uv run --group dev pytest tests/test_advisor.py tests/test_crypto_research.py -v`
- 退出码：0
- 关键输出：
  ```
  collected 33 items

  tests/test_advisor.py::TestAdvisorOverview::test_returns_200_and_schema PASSED
  tests/test_advisor.py::TestAdvisorOverview::test_positions_is_list PASSED
  tests/test_advisor.py::TestAdvisorOverview::test_api_alias_works PASSED
  tests/test_advisor.py::TestCryptoOpportunities::test_neutral_signal_no_items PASSED
  tests/test_advisor.py::TestCryptoOpportunities::test_contrarian_long_produces_item PASSED
  tests/test_advisor.py::TestCryptoOpportunities::test_low_funding_neutral_produces_basis_item PASSED
  tests/test_advisor.py::TestCryptoOpportunities::test_contrarian_short_no_opportunity PASSED
  tests/test_advisor.py::TestCryptoOpportunities::test_api_alias_works PASSED
  tests/test_advisor.py::TestCryptoOpportunities::test_default_symbol_is_btc PASSED
  tests/test_advisor.py::TestCryptoRisks::test_neutral_signal_no_items PASSED
  tests/test_advisor.py::TestCryptoRisks::test_contrarian_short_produces_risk PASSED
  tests/test_advisor.py::TestCryptoRisks::test_high_funding_neutral_produces_elevated_risk PASSED
  tests/test_advisor.py::TestCryptoRisks::test_contrarian_long_no_risk PASSED
  tests/test_advisor.py::TestCryptoRisks::test_api_alias_works PASSED
  tests/test_crypto_research.py::TestResearchLatest::test_happy_path_ranging PASSED
  ... (5 parametrized regime tests) PASSED
  tests/test_crypto_research.py::TestResearchLatest::test_api_alias_works PASSED
  tests/test_crypto_research.py::TestResearchLatest::test_overheated_bull_strategies PASSED
  tests/test_crypto_research.py::TestResearchOptimize::test_happy_path_returns_params PASSED
  ... (5 parametrized + 2 more) PASSED
  tests/test_crypto_research.py::TestResearchOptimizeLatest::test_happy_path PASSED
  tests/test_crypto_research.py::TestResearchOptimizeLatest::test_default_params_structure PASSED
  tests/test_crypto_research.py::TestResearchOptimizeLatest::test_api_alias_works PASSED

  ============================== 33 passed in 6.16s ==============================
  ```

### `uv run --isolated --with mypy python -m mypy src/`
- 退出码：0
- 关键输出：
  ```
  Success: no issues found in 87 source files
  ```

### `git diff main --name-only -- apps/stock-assistant/frontends/workbench/ apps/quant-assistant/ common/`
- 退出码：0
- 关键输出：(空)

---

## 代码 Review 备注

1. **docstring 完整**：advisor.py 和 crypto_research.py 均有模块级 docstring 列出所有端点，符合 CLAUDE.md 规范。

2. **type hints**：所有函数均有明确 return type annotation（`dict[str, Any]`、`tuple[str, float, float]` 等），`from __future__ import annotations` 已引入。

3. **无跨 app import**：advisor.py 和 crypto_research.py 仅 import `quantpilot_stock.*` 和 `quantpilot_common.*`，无 `apps/quant-assistant` 或 `apps/stock-assistant/frontends` 的引用。

4. **async 一致性**：外部 IO（fetch_binance/fetch_okx）用 `asyncio.gather` 并发拉取，符合 async-first 规范。

5. **MVP 范围遵守**：optimize 端点仅返回规则参数，未引入实时网格搜索，符合 task spec "不做什么" 章节。

6. **轻度观察（不阻塞）**：`advisor_overview()` 是同步函数（非 `async def`），但它内部不做 IO（仅访问内存快照），这是合理的；FastAPI 会在线程池中运行同步端点，不影响正确性。

---

## 后续动作

- PASS：可合 PR。提交时建议将四个新文件（advisor.py、crypto_research.py、test_advisor.py、test_crypto_research.py）和本验收记录一起 `git add` 后 commit。
- 更新 `docs/acceptance/INDEX.md` 加入本条目。
