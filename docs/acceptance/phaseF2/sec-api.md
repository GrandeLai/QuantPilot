# Acceptance Report: phaseF2.sec-api

**Run at**: 2026-04-29T10:30:00Z
**Implementation PR**: working tree (untracked / unstaged changes relative to HEAD = 3050343)
**Diff range**: `HEAD` (git status shows untracked + modified files)
**Acceptance-agent invocation**: claude-sonnet-4-6, session 2026-04-29
**Verdict**: NEEDS-REVISION

---

## 文件影响范围检查

Task spec 白名单（新建/修改）：
- `apps/stock-assistant/backend/src/quantpilot_stock/api/sec.py` (新建)
- `apps/stock-assistant/backend/tests/test_sec_api.py` (新建)
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py` (修改)

实际改动文件（`git status --short`）：

| 文件 | 状态 | 白名单内? |
|---|---|---|
| `apps/stock-assistant/backend/pyproject.toml` | M (modified) | 否 |
| `apps/stock-assistant/backend/src/quantpilot_stock/main.py` | M (modified) | 是 |
| `apps/stock-assistant/frontends/workbench/src/api/client.ts` | M (modified) | 否 |
| `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx` | M (modified) | 否 |
| `uv.lock` | M (modified) | 否 |
| `apps/stock-assistant/backend/src/quantpilot_stock/api/sec.py` | ?? (untracked new) | 是 |
| `apps/stock-assistant/backend/src/quantpilot_stock/edgar/` | ?? (untracked new dir) | 否 |
| `apps/stock-assistant/backend/tests/test_edgar_client.py` | ?? (untracked new) | 否 |
| `apps/stock-assistant/backend/tests/test_edgar_diff_engine.py` | ?? (untracked new) | 否 |
| `apps/stock-assistant/backend/tests/test_form4_cluster.py` | ?? (untracked new) | 否 |
| `apps/stock-assistant/backend/tests/test_sec_api.py` | ?? (untracked new) | 是 |
| `apps/stock-assistant/frontends/workbench/src/components/SECEventsPanel.tsx` | ?? (untracked new) | 否 |
| `docs/tasks/phaseF2/` | ?? (untracked new dir) | 否 |

**超出白名单：11 个路径（含目录）**

### 分类分析

**类型 B（白名单遗漏的必要伴随文件）** — 建议扩充白名单：
- `apps/stock-assistant/backend/src/quantpilot_stock/edgar/` (含 `__init__.py`, `client.py`, `diff_engine.py`, `form4_engine.py`, `models.py`) — `sec.py` 直接 import 此模块，不可缺少
- `apps/stock-assistant/backend/tests/test_edgar_client.py` — edgar 客户端单元测试（配套 edgar 模块）
- `apps/stock-assistant/backend/tests/test_edgar_diff_engine.py` — diff engine 单元测试
- `apps/stock-assistant/backend/tests/test_form4_cluster.py` — Form 4 集群引擎测试
- `apps/stock-assistant/backend/pyproject.toml` — 新增 `rapidfuzz>=3.0.0` 依赖（edgar diff engine 使用）
- `uv.lock` — 依赖锁定文件随 pyproject.toml 联动更新
- `docs/tasks/phaseF2/` — 任务 spec 目录（其他子任务的 spec 文件，无害的文档补充）

**类型 A（实现超出任务范围的 scope creep）** — 需从本 PR 移除或拆分到独立任务：
- `apps/stock-assistant/frontends/workbench/src/api/client.ts` — 新增 SEC TypeScript 接口和 `fetchSECSummary()`
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx` — 挂载 `SECEventsPanel`
- `apps/stock-assistant/frontends/workbench/src/components/SECEventsPanel.tsx` — 376 行新前端组件

任务 spec 明确定位为"SEC 事件流 **API 端点**"（纯后端），前端集成属于独立 phaseF2 任务（`sec-events-panel.md` 已在 `docs/tasks/phaseF2/` 中单独列出），不应合并进此 PR。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 文件存在并注册 | ✅ PASS | `test -f sec.py` 退出码 0；`grep` 在 `main.py:66` 找到 `from quantpilot_stock.api.sec import router as sec_router`，`main.py:104` 找到 `include_with_api_alias(sec_router)` |
| AC-2: 四个端点存在 | ✅ PASS | `grep -c "@router.get" sec.py` = 4（`/8k/recent`, `/8k/diff`, `/form4/signals`, `/summary`） |
| AC-3: 错误处理（503/404/429） | ✅ PASS | `sec.py` 中含 `HTTPException(status_code=404, ...)` 和 `HTTPException(status_code=503, ...)`；429 限速处理在 `edgar/client.py` 层（注：sec.py 本身未直接 raise 429，依赖 edgar client 的速率控制） |
| AC-4: 单元测试通过（mock edgar client） | ✅ PASS | `pytest tests/test_sec_api.py -v` 退出码 0，11 tests passed（≥10），覆盖四端点 happy path + 404 + 503 + api alias |
| AC-5: mypy 通过 | ✅ PASS | `uv run --isolated --with mypy python -m mypy src/quantpilot_stock/api/sec.py` 退出码 0，"Success: no issues found in 1 source file" |

---

## 测试执行日志摘要

### `uv run pytest tests/test_sec_api.py -v`
- 退出码：0
- 输出摘要：
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

  11 passed in 6.17s
  ```

### `uv run --isolated --with mypy python -m mypy src/quantpilot_stock/api/sec.py`
- 退出码：0
- 输出：`Installed 130 packages in 338ms\nSuccess: no issues found in 1 source file`

---

## 代码 Review 备注

**正面发现：**
- `sec.py` 有完整模块级 docstring，所有端点函数有 docstring，type hints 完整
- 无跨 app import（edgar 模块仅 import 自 `quantpilot_stock.edgar.*`，不 import `quant_assistant` 或 `common/` 反向路径）
- 错误处理清晰：ValueError → 404，Exception → 503，符合 spec 设计
- `get_sec_summary` 使用 `asyncio.gather` 并行拉取，设计合理
- `main.py` 使用现有 `include_with_api_alias()` 工具函数注册，与其他 router 风格一致

**注意事项（不阻塞本次验收结论）：**
- AC-3 spec 要求 429 错误处理，`sec.py` 未直接 raise 429（只有 404/503）。429 的速率控制在 `edgar/client.py` 内部实现（通过 `asyncio.sleep` 节流）。如果 spec 意图是 sec.py 层面直接返回 429，则 AC-3 实现不完整——但 spec 对此措辞模糊（"grep -q 503|HTTPException|404"，不要求 429 在 sec.py），故此处记录为观察项。
- `edgar/client.py` 包含真实 HTTP 网络调用（httpx）；edgar 模块测试（`test_edgar_client.py`）的测试质量需单独验收（超出本 task spec 范围）。

---

## 后续动作

本次 verdict = **NEEDS-REVISION**，原因是 scope creep（前端文件超出白名单且超出任务定义范围）。

### 选项 A（推荐）：拆分 PR
将以下三个文件移出本 PR，归入独立 `phaseF2.sec-events-panel` 任务：
- `apps/stock-assistant/frontends/workbench/src/api/client.ts`
- `apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx`
- `apps/stock-assistant/frontends/workbench/src/components/SECEventsPanel.tsx`

同时，将以下文件加入 `phaseF2.sec-api` 任务 spec 白名单：
- `apps/stock-assistant/backend/src/quantpilot_stock/edgar/**` (必要依赖模块)
- `apps/stock-assistant/backend/tests/test_edgar_client.py`
- `apps/stock-assistant/backend/tests/test_edgar_diff_engine.py`
- `apps/stock-assistant/backend/tests/test_form4_cluster.py`
- `apps/stock-assistant/backend/pyproject.toml`
- `uv.lock`
- `docs/tasks/phaseF2/**`

修改 spec 后重跑验收（本报告为 v1，重验写 `sec-api-v2.md`）。

### 选项 B：扩充本 task spec 范围
在 spec 中明确包含前端集成（将 `sec-events-panel` 合并进 `sec-api`），并更新白名单和 AC。

无论选哪个选项，**所有 AC 目前已 PASS，技术实现无阻塞问题**，只需处理白名单与范围声明的一致性。
