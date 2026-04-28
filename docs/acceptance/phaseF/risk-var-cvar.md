# Acceptance Report: phaseF.risk-var-cvar

> **v2 — re-acceptance after spec whitelist update**
> v1 verdict was FAIL (run 2026-04-29) due to 4 doc renames outside the whitelist.
> Resolution: task spec `docs/tasks/phaseF/risk-var-cvar.md` updated in commit `d762974`
> to add those 4 R100 renames as "type-c: parallel process contamination, post-hoc
> whitelisted". The renames are zero-content moves belonging to phaseE.docs-cleanup-refresh
> (merged via 854ebfb + e59a73d). User accepted the post-hoc whitelist widening.

**Run at**: 2026-04-29T02:00:00Z
**Implementation commit**: `93e8a92`
**Spec update commit**: `d762974`
**Diff range**: `93e8a92^..93e8a92`
**Acceptance-agent invocation**: v2
**Verdict**: PASS

---

## 文件影响范围检查

`git diff --name-only 93e8a92^..93e8a92` 输出共 8 个路径：

| 文件 | 白名单状态 |
|---|---|
| `apps/stock-assistant/backend/src/quantpilot_stock/risk/__init__.py` | 允许（修改） |
| `apps/stock-assistant/backend/src/quantpilot_stock/risk/var_cvar.py` | 允许（新建） |
| `apps/stock-assistant/backend/tests/test_risk_var_cvar.py` | 允许（新建） |
| `docs/tasks/phaseF/risk-var-cvar.md` | 允许（task spec 本身） |
| `docs/archive/legacy/Claude_Code_Usage_Guide.md` | 允许（type-c：R100 rename，v2 白名单追认） |
| `docs/archive/legacy/factor_guide.md` | 允许（type-c：R100 rename，v2 白名单追认） |
| `docs/archive/legacy/llm-agent-layer-design.md` | 允许（type-c：R100 rename，v2 白名单追认） |
| `docs/archive/legacy/tab-pages-guide.md` | 允许（type-c：R100 rename，v2 白名单追认） |

这 4 个路径均为 R100（100% 相似度，零内容变更），已由更新后的 task spec 显式追认为"捎带"异常。`pyproject.toml` 未出现在 diff 中（满足 AC-7 硬约束）。

**文件范围结论：全部 8 个路径均在白名单内。无违规。**

---

## 测试执行日志摘要

### 1. 单测全过（AC-4）
```
pytest tests/test_risk_var_cvar.py -v
18 collected, 18 passed in 2.78s
EXIT: 0
```

### 2. ruff（AC-5）
```
uv run --with ruff ruff check src/quantpilot_stock/risk/ tests/test_risk_var_cvar.py
All checks passed!
EXIT: 0
```

### 3. mypy（AC-6）
```
uv run --with mypy mypy src/quantpilot_stock/risk/ --ignore-missing-imports
Success: no issues found in 5 source files
EXIT: 0
```

### 4. import 烟雾测试（AC-3）
```
uv run python -c "from quantpilot_stock.risk import historical_var, historical_cvar, parametric_var, var_summary; print('ok')"
ok
EXIT: 0
```

### 5. 现有测试不回归（AC-8）
```
pytest tests/ -x --ignore=tests/test_risk_var_cvar.py -q
217 passed in 8.87s
EXIT: 0
```

### 6. pyproject.toml 未改（AC-7）
```
git diff main -- apps/stock-assistant/backend/pyproject.toml
(no output)
EXIT: 0
```

### 7. 前两批 risk 导出未破坏（AC-9）
```
uv run python -c "from quantpilot_stock.risk import kelly_fraction_binary, vol_target_recommendation, analyze_strategy_decay; print('ok')"
ok
EXIT: 0
```

---

## AC 逐条核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: `var_cvar.py` 存在 | PASS | 文件在 diff 中新建，`test -f` 返回 0 |
| AC-2: `test_risk_var_cvar.py` 存在 | PASS | 文件在 diff 中新建，`test -f` 返回 0 |
| AC-3: 4 个新函数可从顶包 import | PASS | smoke test 退出码 0，输出 `ok` |
| AC-4: 单测全过，数量 >= 14 | PASS | 18 tests collected, 18 passed; 18 >= 14 |
| AC-5: ruff 干净 | PASS | `All checks passed!`，退出码 0 |
| AC-6: mypy 干净 | PASS | `Success: no issues found in 5 source files`，退出码 0 |
| AC-7: pyproject.toml 未改 | PASS | diff 输出为空，退出码 0 |
| AC-8: 现有测试无回归 | PASS | `217 passed in 8.87s`，退出码 0 |
| AC-9: F.1.1/1.2 导出未破坏 | PASS | 退出码 0，输出 `ok` |
| **文件范围** | **PASS** | 4 个 R100 rename 已在 v2 白名单中追认 |

所有 AC 均为 PASS，无 PARTIAL，无 FAIL。

---

## 代码 Review 备注

（与 v1 一致，无变更，均为信息性记录）

1. `var_cvar.py` 有模块级 docstring，清晰说明返回约定（正数 = 亏损绝对值）和范围边界（EVT 等延后），符合 CLAUDE.md Python 规范。
2. 所有 4 个公共函数带完整 type hints，内部 helper `_validate` 亦有明确类型。
3. 实现符合 task spec 算法描述：`historical_var` 用 `np.quantile(arr, 1-confidence)` + `max(-q, 0)`；`historical_cvar` 取尾部均值；`parametric_var` 用 `scipy.stats.norm.ppf`；`var_summary` 一站式聚合。
4. 无跨 app import，无新依赖引入（scipy 已在 pyproject.toml 中）。
5. 测试覆盖正常路径、边界（全正收益 VaR=0、零方差 parametric_var=0）、错误路径（confidence 越界、样本不足、method 非法），18 total 超出 14 下限。

---

## 后续动作

PASS — PR 可合。无修复项。

建议流程改进（已在 task spec 中记录）：每个新 task 开干前必须 `git status` 确认工作树干净，避免并行会话的 staged 改动混入当前 commit。
