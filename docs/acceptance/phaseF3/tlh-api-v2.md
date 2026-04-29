# Acceptance Report: phaseF3.tlh-api

**Run at**: 2026-04-29T10:30:00Z
**Implementation PR**: commit e00cb1a (feat: Phase F.3 TLH + TWAP/VWAP + TCA 全栈实现)
**Diff range**: `HEAD~1..HEAD` (e00cb1a)
**Acceptance-agent invocation**: claude-sonnet-4-6, 2026-04-29 (v2 re-run)
**Verdict**: PASS

---

## 文件影响范围检查

- 改动文件总数（`git diff HEAD~1 HEAD --name-only`）：25
- 与 tlh-api 白名单相关：3（全在白名单内）
  - `apps/stock-assistant/backend/src/quantpilot_stock/api/tlh.py` ✅ (新建)
  - `apps/stock-assistant/backend/tests/test_tlh_api.py` ✅ (新建)
  - `apps/stock-assistant/backend/src/quantpilot_stock/main.py` ✅ (修改，注册 tlh_router)
- `main.py` 同时注册了 `execution_router`，但 execution-api 已有独立 task spec 并已通过 PASS 验收（execution-api.md），属于合法批次伴随改动。
- 其余文件属于同批次其他任务，均有各自对应 task spec。
- 批次按 task spec "批次开发说明" 执行，clean working tree 条件满足。

**判定**：所有白名单文件均存在，额外改动有合法归属，不影响本 task 验收。

---

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 文件存在并注册（api/tlh.py + main.py 含 tlh_router/from...tlh...import） | ✅ PASS | `test -f` 退出码 0；`grep -q "tlh_router\|from.*tlh.*import" main.py` 命中 |
| AC-2: 端点数量（`grep -c "@router\."` >= 3） | ✅ PASS | 输出 `3`；三个端点：POST /scan、GET /replacement、POST /estimate-saving |
| AC-3: 测试通过（>= 8 个） | ✅ PASS | `pytest tests/test_tlh_api.py -v` 退出码 0，**15 passed in 0.10s** |
| AC-4: mypy 通过 | ✅ PASS | `uv run --isolated --with mypy python -m mypy src/quantpilot_stock/api/tlh.py` 退出码 0，"Success: no issues found in 1 source file" |

---

## 测试执行日志摘要

### `bash -l -c 'cd apps/stock-assistant/backend && uv run pytest tests/test_tlh_api.py -v'`
- 退出码：0
- 收集：15 items
- 结果：**15 passed in 0.10s**
- 覆盖：
  - TestTLHScan (8 tests): returns candidate、returns estimated saving、no candidates above threshold、wash sale flag、generated_at present、scan via api prefix、long term lot、short term lot
  - TestTLHReplacement (3 tests): SPY replacement、unknown ticker empty list、lowercase ticker normalized
  - TestTLHEstimateSaving (4 tests): estimate saving short term、estimate saving long term、estimate saving returns details、estimate saving empty candidates

### `grep -c "@router\." apps/stock-assistant/backend/src/quantpilot_stock/api/tlh.py`
- 退出码：0
- 输出：`3`（满足 >= 3）

### `bash -l -c 'cd apps/stock-assistant/backend && uv run --isolated --with mypy python -m mypy src/quantpilot_stock/api/tlh.py'`
- 退出码：0
- 输出：`Success: no issues found in 1 source file`

---

## 代码 Review 备注

- `api/tlh.py` 有完整模块级 docstring，列出三个端点及免责声明。
- 所有 Pydantic 模型均有 Field 约束（如 `Field(gt=0)` 对 quantity/cost_basis）。
- 三个端点均有详细 docstring 说明请求/响应语义。
- 错误处理：所有端点均有 `try/except`，捕获异常后返回 HTTP 503 + loguru 日志。
- 无跨 app import（仅用 fastapi/pydantic/loguru + 同项目 tlh.engine）。
- `main.py` 额外注册了 `execution_router`，该功能有独立 task spec（phaseF3.execution-api）且已 PASS，属于合法批次改动。

---

## 后续动作

- PASS：可合入 PR。其余同批次 task（tlh-engine、tlh-panel）同步验收后统一合入。
