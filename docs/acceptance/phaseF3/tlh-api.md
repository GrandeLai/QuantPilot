# Acceptance Report: phaseF3.tlh-api

**Run at**: 2026-04-29T09:42:09Z
**Implementation PR**: working tree (uncommitted changes vs HEAD b69856f)
**Diff range**: `HEAD` (git diff HEAD — modified tracked files + untracked new files)
**Acceptance-agent invocation**: claude-sonnet-4-6, 2026-04-29
**Verdict**: NEEDS-REVISION

---

## 文件影响范围检查

- 改动文件总数（tracked, `git diff --name-only HEAD`）：3
- 在白名单内（tlh-api 白名单）：1
- 超出白名单：2

```
apps/stock-assistant/backend/src/quantpilot_stock/main.py      ✅ 在白名单内
apps/stock-assistant/frontends/workbench/src/api/client.ts     ❌ 属于 phaseF3.tlh-panel 白名单
apps/stock-assistant/frontends/workbench/src/components/workbench/RiskReviewCenter.tsx ❌ 属于 phaseF3.tlh-panel 白名单
```

**补充说明**：`main.py` 的变更除了注册 `tlh_router`（在白名单内）之外，还注册了 `execution_router`，
后者属于尚未定义 task spec 的 execution 功能。这是额外的 scope creep（顺带加了不属于 tlh-api 的改动）。

tlh-api 白名单内的新文件（`api/tlh.py`、`tests/test_tlh_api.py`）均为 untracked 新文件，
未出现在 `git diff --name-only HEAD` 中（因实现尚未提交）。

这是多 task 实现共存于同一工作树导致的 scope 交叉，属于 NEEDS-REVISION 类型 (a)：
implementation agent 应将各 task 分开 commit。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 文件存在并注册（api/tlh.py + main.py 含 tlh_router/from...tlh...import） | ✅ PASS | `test -f` 通过；`grep -q "tlh_router\|from.*tlh.*import" main.py` 命中（两条导入均存在） |
| AC-2: 端点数量（`grep -c "@router\."` >= 3） | ✅ PASS | 输出 `3`，满足 >= 3；三个端点：POST /scan、GET /replacement、POST /estimate-saving |
| AC-3: 测试通过（>= 8 个） | ✅ PASS | `pytest tests/test_tlh_api.py -v` 退出码 0，**15 passed**（>= 8 满足） |
| AC-4: mypy 通过 | ✅ PASS | `uv run --isolated --with mypy python -m mypy src/quantpilot_stock/api/tlh.py` 退出码 0，"Success: no issues found in 1 source file" |

---

## 测试执行日志摘要

### `uv run pytest tests/test_tlh_api.py -v`
- 退出码：0
- 收集：15 items
- 结果：**15 passed in 0.08s**
- 覆盖：TestTLHScan (8)、TestTLHReplacement (3)、TestTLHEstimateSaving (4)

### `grep -c "@router\." api/tlh.py`
- 输出：`3`（满足 >= 3）

### `uv run --isolated --with mypy python -m mypy src/quantpilot_stock/api/tlh.py`
- 退出码：0
- 输出：`Success: no issues found in 1 source file`

---

## 代码 Review 备注

- `api/tlh.py` 有完整模块级 docstring，列出所有三个端点及免责声明。
- 所有 Pydantic 模型均有 Field 约束（如 `Field(gt=0)` 对 quantity/cost_basis）。
- 三个端点均有详细 docstring 说明请求/响应语义。
- `_to_response` / `_from_response` 是内部工具函数，正确完成 TLHCandidate ↔ CandidateResponse 的双向转换。
- 错误处理：所有端点均有 `try/except`，捕获异常后返回 HTTP 503 + loguru 日志。
- 无跨 app import（仅用 fastapi/pydantic/loguru + 同项目 tlh.engine）。
- `main.py` 额外注册了 `execution_router`（不属于本任务白名单）：
  - `from quantpilot_stock.api.execution import router as execution_router` (L68)
  - `include_with_api_alias(execution_router)` (L108)
  - 这是 scope creep，应在 execution 相关 task spec 中处理。

---

## 后续动作

**NEEDS-REVISION 原因（双重）**：
1. `client.ts` 和 `RiskReviewCenter.tsx` 的修改属于 phaseF3.tlh-panel 白名单，不应出现在 tlh-api 的 PR diff 中。
2. `main.py` 中除 tlh_router 注册外，还额外注册了 execution_router（属于另一 task，尚无 spec），是任务范围外的 scope creep。

**建议**：
1. 将 tlh-api 白名单内的文件单独 commit（`api/tlh.py`、`tests/test_tlh_api.py`、以及 `main.py` 仅含 tlh_router 的变更）；
2. `execution_router` 注册应在其对应 task spec 创建后，由专门 commit 处理；
3. 分开 commit 后重跑本次验收（`-v2` 报告）。

如用户接受"多 task 合并一次 commit"的方式，可在确认后给出 PASS；
所有 AC 测试本次均已通过（15/15 passed，3 endpoints，mypy clean）。
