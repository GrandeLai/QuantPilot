# Acceptance Report: phaseF.risk-engine-core

**Run at**: 2026-04-28T00:00:00Z
**Implementation commit**: `0ef629c`
**Diff range**: `0ef629c^..0ef629c`
**Acceptance-agent invocation**: v1
**Verdict**: PASS

## 文件影响范围检查

- 改动文件总数：6
- 在白名单内：6
- 超出白名单：0

明细：
- `apps/stock-assistant/backend/src/quantpilot_stock/risk/__init__.py` — 白名单（新建）
- `apps/stock-assistant/backend/src/quantpilot_stock/risk/kelly.py` — 白名单（新建）
- `apps/stock-assistant/backend/src/quantpilot_stock/risk/vol_target.py` — 白名单（新建）
- `apps/stock-assistant/backend/tests/test_risk_kelly_vol.py` — 白名单（新建）
- `docs/tasks/phaseF/README.md` — 白名单（明确列出）
- `docs/tasks/phaseF/risk-engine-core.md` — 白名单（本 spec）

`pyproject.toml` 未出现在 diff 中，满足"不允许改"约束。

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 三个模块文件存在 | PASS | `__init__.py`、`kelly.py`、`vol_target.py` 均在 diff 中新建，Read 确认内容完整 |
| AC-2: 测试文件存在 | PASS | `tests/test_risk_kelly_vol.py` 在 diff 中新建 |
| AC-3: 全部 8 个公共函数可从顶包 import | PASS | smoke test 退出码 0，输出 `ok` |
| AC-4: 单测全过，数量 ≥ 18 | PASS | 34 tests collected, 34 passed (0.30s)，退出码 0；34 >> 18 |
| AC-5: ruff 干净 | PASS | `All checks passed!`，退出码 0 |
| AC-6: mypy 干净 | PASS | `Success: no issues found in 3 source files`，退出码 0 |
| AC-7: pyproject.toml 未改 | PASS | `git diff main -- .../pyproject.toml` 输出为空，退出码 0 |
| AC-8: 不修改其它 app | PASS | `git diff main -- apps/quant-assistant/ common/` 无 `^[-+]` 行，退出码 0 |
| AC-9: 现有测试无回归 | PASS | `165 passed in 7.95s`，退出码 0（--ignore=test_risk_kelly_vol.py） |

## 测试执行日志摘要

### 1. 单测全过
```
pytest tests/test_risk_kelly_vol.py -v
34 collected, 34 passed in 0.30s
EXIT: 0
```

### 2. ruff
```
uv run --with ruff ruff check src/quantpilot_stock/risk/ tests/test_risk_kelly_vol.py
All checks passed!
EXIT: 0
```

### 3. mypy
```
uv run --with mypy mypy src/quantpilot_stock/risk/ --ignore-missing-imports
Success: no issues found in 3 source files
EXIT: 0
```

### 4. import 烟雾测试
```
uv run python -c "from quantpilot_stock.risk import ..."
ok
EXIT: 0
```

### 5. 现有测试不回归
```
pytest tests/ -x --ignore=tests/test_risk_kelly_vol.py -q
165 passed in 7.95s
EXIT: 0
```

### 6. pyproject.toml 未改
```
git diff main -- apps/stock-assistant/backend/pyproject.toml
(no output)
EXIT: 0
```

## 代码 Review 备注

1. 三个新文件均有模块级 docstring，符合 CLAUDE.md Python 规范。
2. 所有公共函数均带完整 type hints（`float`、`np.ndarray`、`dict[str, float | str]`、`Literal` 返回类型），满足项目规范。
3. 无跨 app import：`kelly.py` 和 `vol_target.py` 仅引用 `numpy`；`__init__.py` 仅 re-export 同包函数。
4. `vol_target.py` 使用 `Literal["low", "normal", "high", "crisis"]` 定义 `Regime` 类型，属于良好实践。
5. 没有引入任何新依赖（仅使用已有的 numpy），满足"不引入新依赖"约束。
6. 测试文件覆盖每个函数的正常路径、边界值和错误输入，每函数不少于 2 个用例（34 total 远超 18 下限）。
7. 实现严格限定在 `quantpilot_stock.risk` 子包内，无"顺带重构"。

## 后续动作

PASS — PR 可合。本任务为 F.1.1，下游任务 F.1.2（Sharpe 衰减）、F.1.3（VaR/CVaR）、F.1.4（API 路由）可直接消费本包内的纯函数。
