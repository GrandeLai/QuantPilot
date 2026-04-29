# Acceptance Report: phaseF2.sec-api (v2)

**Run at**: 2026-04-29T11:00:00Z
**Implementation PR**: commit d2eca0d (feat(edgar): SEC 三合一事件流 — 8-K diff + Form 4 cluster + panel)
**Diff range**: `git diff HEAD~1..HEAD`
**Acceptance-agent invocation**: claude-sonnet-4-6, session 2026-04-29 v2
**Verdict**: PASS

---

## Context (v2 re-run)

v1 report (`sec-api.md`) returned **NEEDS-REVISION** because files were uncommitted (working tree state) and several out-of-whitelist files had not yet been assigned to their spec. Since then:
1. All phaseF2 files have been committed in a single batch commit (`d2eca0d`).
2. The `sec-api.md` spec's "文件影响范围" section now explicitly enumerates the edgar dependency modules under "依赖（由 F.2.1–F.2.3 提供，批次共同提交）", resolving the edgar-module whitelist ambiguity.
3. The frontend files (`SECEventsPanel.tsx`, `RiskReviewCenter.tsx`, `client.ts`) are covered by the separate `phaseF2.sec-events-panel` task spec (own whitelist, own AC).

---

## 文件影响范围检查

**Task spec 白名单**（核心 + 依赖）：

| 文件 | 类别 |
|---|---|
| `apps/stock-assistant/backend/src/quantpilot_stock/api/sec.py` | 核心新建 |
| `apps/stock-assistant/backend/tests/test_sec_api.py` | 核心新建 |
| `apps/stock-assistant/backend/src/quantpilot_stock/main.py` | 核心修改 |
| `apps/stock-assistant/backend/src/quantpilot_stock/edgar/__init__.py` | 依赖（F.2.1，批次共提） |
| `apps/stock-assistant/backend/src/quantpilot_stock/edgar/models.py` | 依赖（F.2.1，批次共提） |
| `apps/stock-assistant/backend/src/quantpilot_stock/edgar/client.py` | 依赖（F.2.1，批次共提） |
| `apps/stock-assistant/backend/src/quantpilot_stock/edgar/diff_engine.py` | 依赖（F.2.2，批次共提） |
| `apps/stock-assistant/backend/src/quantpilot_stock/edgar/form4_engine.py` | 依赖（F.2.3，批次共提） |
| `apps/stock-assistant/backend/pyproject.toml` | 依赖（rapidfuzz，批次共提） |
| `uv.lock` | 依赖锁定（联动） |
| `apps/stock-assistant/backend/tests/test_edgar_client.py` | 依赖测试（F.2.1，批次共提） |
| `apps/stock-assistant/backend/tests/test_edgar_diff_engine.py` | 依赖测试（F.2.2，批次共提） |
| `apps/stock-assistant/backend/tests/test_form4_cluster.py` | 依赖测试（F.2.3，批次共提） |
| `docs/tasks/phaseF2/**` | 任务 spec 文档（无害） |
| `docs/acceptance/phaseF2/**` | 验收记录（无害） |

**批次共提但属于其他 task spec 的文件**（不纳入本任务白名单，由 sec-events-panel 覆盖）：

| 文件 | 归属 |
|---|---|
| `apps/stock-assistant/frontends/workbench/src/components/SECEventsPanel.tsx` | phaseF2.sec-events-panel |
| `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx` | phaseF2.sec-events-panel |
| `apps/stock-assistant/frontends/workbench/src/api/client.ts` | phaseF2.sec-events-panel |

这三个文件有独立 task spec 和独立验收流程，不视为 sec-api 的 scope creep。

**结论**：文件影响范围 **合格**（所有非前端文件均在扩展白名单内；前端文件属别任务）。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 文件存在并注册 | PASS | `test -f apps/.../api/sec.py` 退出码 0；`grep` 在 `main.py:66` 找到 `from quantpilot_stock.api.sec import router as sec_router`，`main.py:104` 找到 `include_with_api_alias(sec_router)` |
| AC-2: 四个端点存在 | PASS | `grep -c "@router.get" sec.py` = 4（`/8k/recent`、`/8k/diff`、`/form4/signals`、`/summary`） |
| AC-3: 错误处理（503/404） | PASS | `grep -q "503\|HTTPException\|404"` 退出码 0；sec.py 含 HTTPException 导入 + status_code=404（3 处）+ status_code=503（3 处）|
| AC-4: 单元测试通过 | PASS | `pytest tests/test_sec_api.py -v` 退出码 0，11 tests collected，11 passed（≥10 阈值满足）|
| AC-5: mypy 通过 | PASS | `uv run --isolated --with mypy python -m mypy src/quantpilot_stock/api/sec.py` 退出码 0，"Success: no issues found in 1 source file" |

所有 AC 均 PASS，无 PARTIAL 或 FAIL 项。

---

## 测试执行日志摘要

### AC-1 文件检查
```
test -f apps/stock-assistant/backend/src/quantpilot_stock/api/sec.py  →  exit 0
grep main.py → line 66: from quantpilot_stock.api.sec import router as sec_router
              line 104: include_with_api_alias(sec_router)
```

### AC-2 端点计数
```
grep -c "@router.get" sec.py → 4
```

### AC-3 错误处理
```
grep -q "503\|HTTPException\|404" sec.py → exit 0
匹配: line 18 (import), 103 (404), 106 (503), 142 (404), 145 (503), 176 (404), 179 (503)
```

### AC-4 pytest
```
collected 11 items

tests/test_sec_api.py::TestGet8KRecent::test_happy_path PASSED
tests/test_sec_api.py::TestGet8KRecent::test_ticker_not_found_returns_404 PASSED
tests/test_sec_api.py::TestGet8KRecent::test_network_error_returns_503 PASSED
tests/test_sec_api.py::TestGet8KRecent::test_api_alias_works PASSED
tests/test_sec_api.py::TestGet8KDiff::test_happy_path_with_two_filings PASSED
tests/test_sec_api.py::TestGet8KDiff::test_fewer_than_two_filings PASSED
tests/test_sec_api.py::TestGetForm4Signals::test_happy_path_with_cluster PASSED
tests/test_sec_api.py::TestGetForm4Signals::test_404_on_unknown_ticker PASSED
tests/test_sec_api.py::TestGetSECSummary::test_happy_path PASSED
tests/test_sec_api.py::TestGetSECSummary::test_empty_data_graceful PASSED
tests/test_sec_api.py::TestGetSECSummary::test_api_alias PASSED

11 passed in 5.73s  →  exit 0
```

### AC-5 mypy
```
Installed 130 packages in 342ms
Success: no issues found in 1 source file  →  exit 0
```

---

## 代码 Review 备注

1. **模块级 docstring + type hints**：`sec.py` 有完整模块级 docstring（中英文说明端点和限速），所有端点函数有 docstring，参数和返回值均有 type annotations（`dict[str, Any]`）。符合 CLAUDE.md 规范。
2. **无跨 app import**：`sec.py` 仅 import 自 `quantpilot_stock.edgar.*`（同 app），无 `quant_assistant` 或 `common/` 反向引用。
3. **错误处理层次清晰**：`ValueError` → 404（ticker 不存在），`Exception` → 503（网络/EDGAR 错误）；`get_sec_summary` 对子任务错误使用 `try/except` + warning log 而非直接 503，符合 summary 端点"容错聚合"的设计意图。
4. **asyncio.gather 并行化**：`get_sec_summary` 并行拉取 8-K 和 Form4 数据，设计合理。
5. **main.py 注册方式**：使用 `include_with_api_alias()` 模式，与 gex、security 等其他 router 一致。

**观察项（非阻塞）**：
- AC-3 spec 措辞含 "429"，但 `sec.py` 不直接 raise 429（429 速率控制在 `edgar/client.py` 层的 `asyncio.sleep` 节流实现）。spec 的 grep 命令仅检查 `503\|HTTPException\|404`，不要求 429 出现在 sec.py，因此 AC-3 判定 PASS。若后续需要显式 429 pass-through，可在 edgar client 抛出专用异常后在 sec.py 捕获并转发。

---

## 结论

全部 5 项 AC PASS，文件影响范围合规（edgar 依赖在 spec 中显式声明为批次共提；前端文件属独立 task）。

**Verdict: PASS**
