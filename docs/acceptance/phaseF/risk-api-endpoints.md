# Acceptance Report: phaseF.risk-api-endpoints

**Run at**: 2026-04-28T00:00:00Z
**Implementation commit**: `17e4de9`
**Diff range**: `17e4de9^..17e4de9`
**Acceptance-agent invocation**: v1
**Verdict**: PASS

---

## 文件影响范围检查

`git diff --name-only 17e4de9^..17e4de9` 输出共 4 个路径：

| 文件 | 白名单状态 |
|---|---|
| `apps/stock-assistant/backend/src/quantpilot_stock/api/risk.py` | 允许（新建） |
| `apps/stock-assistant/backend/src/quantpilot_stock/main.py` | 允许（修改） |
| `apps/stock-assistant/backend/tests/test_risk_api.py` | 允许（新建） |
| `docs/tasks/phaseF/risk-api-endpoints.md` | 允许（task spec 本身） |

`pyproject.toml` 未出现在 diff 中（满足 AC-8 硬约束）。

**文件范围结论：全部 4 个路径均在白名单内。无违规。**

---

## 测试执行日志摘要

### 1. 单测全过（AC-5）
```
pytest tests/test_risk_api.py -v
17 collected, 17 passed in 6.41s
EXIT: 0
```

### 2. ruff（AC-6）
```
uv run --with ruff ruff check src/quantpilot_stock/api/risk.py tests/test_risk_api.py src/quantpilot_stock/main.py
All checks passed!
EXIT: 0
```

### 3. mypy（AC-7）
```
uv run --with mypy mypy src/quantpilot_stock/api/risk.py --ignore-missing-imports
Success: no issues found in 1 source file
EXIT: 0
```

### 4. 现有测试无回归（AC-9）
```
pytest tests/ -x --ignore=tests/test_risk_api.py -q
235 passed in 10.23s
EXIT: 0
```

### 5. pyproject.toml 未改（AC-8）
```
git diff main -- apps/stock-assistant/backend/pyproject.toml
(no output)
EXIT: 0
```

### 6. main.py risk_router 注册确认（AC-3 / AC-4）
```
grep -n "risk_router\|risk\.py" apps/stock-assistant/backend/src/quantpilot_stock/main.py
74:    from quantpilot_stock.api.risk import router as risk_router
94:    include_with_api_alias(risk_router)
EXIT: 0
```

---

## AC 逐条核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: `api/risk.py` 存在 | PASS | 文件在 diff 中新建；`test -f` 返回 0 |
| AC-2: `tests/test_risk_api.py` 存在 | PASS | 文件在 diff 中新建；`test -f` 返回 0 |
| AC-3: `from quantpilot_stock.api.risk import router as risk_router` 出现在 main.py | PASS | grep 退出码 0，行 74 |
| AC-4: `include_with_api_alias(risk_router)` 出现在 main.py | PASS | grep 退出码 0，行 94 |
| AC-5: 单测全过，数量 ≥ 12 | PASS | 17 collected, 17 passed；17 ≥ 12 |
| AC-6: ruff 干净 | PASS | `All checks passed!`，退出码 0 |
| AC-7: mypy 干净 | PASS | `Success: no issues found in 1 source file`，退出码 0 |
| AC-8: pyproject.toml 未改 | PASS | diff 输出为空，退出码 0 |
| AC-9: 现有测试无回归 | PASS | `235 passed in 10.23s`，退出码 0 |
| AC-10: POST /api/risk/kelly 返回 200（TestClient 验证） | PASS | `test_binary_mode_happy_path` 断言 status_code == 200 且通过；路由经 `include_with_api_alias` 注册，端点可及 |

所有 AC 均为 PASS，无 PARTIAL，无 FAIL。

---

## 代码 Review 备注

1. `risk.py` 有模块级 docstring，列出全部 5 个端点路由，符合 CLAUDE.md Python 规范。
2. 所有 Pydantic 模型字段使用完整 type hints；路由函数返回类型均为 `dict[str, Any]`。
3. `ValueError` 统一在 try/except 中包成 `HTTPException(400)`，与 task spec 错误处理要求一致。
4. 无跨 app import；所有 import 来自 `quantpilot_stock.risk`（同 app 内上游引擎）。
5. `KellyRequest.fraction` 和 `cap` 使用 `Field(gt=0.0, le=1.0)` 做 Pydantic 校验，参数越界自动触发 422，而引擎层 `ValueError` 触发 400，两层防御均存在。
6. `POST /risk/summary` 的 `sharpe_decay` 退化逻辑（样本 < recent + baseline + 10 时返回 `None`）经 `test_short_history_skips_decay` 明确覆盖。
7. 测试 17 个，覆盖：5 个端点 happy path、缺字段（binary 模式）、空列表（returns / confidences）、样本不足（vol_target / sharpe_decay / var / summary），满足 task spec "至少一个错误路径"要求。

---

## 后续动作

PASS — PR 可合。无修复项。
