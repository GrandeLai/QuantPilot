# Acceptance Report: phaseF.risk-sharpe-decay

**Run at**: 2026-04-29T00:00:00Z
**Implementation commit**: `4d912d2`
**Diff range**: `4d912d2^..4d912d2`
**Acceptance-agent invocation**: v1
**Verdict**: PASS

## 文件影响范围检查

- 改动文件总数：4
- 在白名单内：4
- 超出白名单：0

明细：
- `apps/stock-assistant/backend/src/quantpilot_stock/risk/sharpe_decay.py` — 白名单（新建）
- `apps/stock-assistant/backend/src/quantpilot_stock/risk/__init__.py` — 白名单（修改，追加 4 export）
- `apps/stock-assistant/backend/tests/test_risk_sharpe_decay.py` — 白名单（新建）
- `docs/tasks/phaseF/risk-sharpe-decay.md` — 白名单（本 spec）

`pyproject.toml` 未出现在 diff 中，满足"不允许改"约束。

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: `sharpe_decay.py` 存在 | PASS | 文件在 diff 中新建，`test -f` 返回 0 |
| AC-2: `test_risk_sharpe_decay.py` 存在 | PASS | 文件在 diff 中新建，`test -f` 返回 0 |
| AC-3: 4 个新函数可从顶包 import | PASS | smoke test 退出码 0，输出 `ok` |
| AC-4: 单测全过，数量 ≥ 12 | PASS | 18 tests collected, 18 passed (0.33s)，退出码 0；18 ≥ 12 |
| AC-5: ruff 干净 | PASS | `All checks passed!`，退出码 0 |
| AC-6: mypy 干净 | PASS | `Success: no issues found in 4 source files`，退出码 0 |
| AC-7: pyproject.toml 未改 | PASS | `git diff main -- .../pyproject.toml` 输出为空，退出码 0 |
| AC-8: 现有测试无回归 | PASS | `199 passed in 7.62s`，退出码 0（--ignore=test_risk_sharpe_decay.py） |
| AC-9: F.1.1 导出未破坏 | PASS | `from quantpilot_stock.risk import kelly_fraction_binary, vol_target_recommendation` 退出码 0，输出 `ok` |

## 测试执行日志摘要

### 1. 单测全过
```
pytest tests/test_risk_sharpe_decay.py -v
18 collected, 18 passed in 0.33s
EXIT: 0
```

### 2. ruff
```
uv run --with ruff ruff check src/quantpilot_stock/risk/ tests/test_risk_sharpe_decay.py
All checks passed!
EXIT: 0
```

### 3. mypy
```
uv run --with mypy mypy src/quantpilot_stock/risk/ --ignore-missing-imports
Success: no issues found in 4 source files
EXIT: 0
```

### 4. import 烟雾测试（4 新函数）
```
uv run python -c "from quantpilot_stock.risk import rolling_sharpe, sharpe_z_score, decay_alert_level, analyze_strategy_decay; print('ok')"
ok
EXIT: 0
```

### 5. 现有测试不回归
```
pytest tests/ -x --ignore=tests/test_risk_sharpe_decay.py -q
199 passed in 7.62s
EXIT: 0
```

### 6. pyproject.toml 未改
```
git diff main -- apps/stock-assistant/backend/pyproject.toml
(no output)
EXIT: 0
```

### 7. F.1.1 导出未破坏
```
uv run python -c "from quantpilot_stock.risk import kelly_fraction_binary, vol_target_recommendation; print('ok')"
ok
EXIT: 0
```

## 代码 Review 备注

1. `sharpe_decay.py` 有模块级 docstring，引用 Bailey & Lopez de Prado (2014)，符合 CLAUDE.md Python 规范。
2. 所有 4 个公共函数带完整 type hints：`np.ndarray`、`float`、`Literal["green","yellow","red"]`、`dict[str, float | str | int]` 均明确标注，满足项目规范。
3. 无跨 app import：`sharpe_decay.py` 仅引用 `numpy` 和标准库；`__init__.py` 仅 re-export 同包函数。
4. `AlertLevel = Literal["green", "yellow", "red"]` 本地类型别名属于良好实践，与 F.1.1 中 `Regime` 的风格一致。
5. 没有引入任何新依赖（仅使用已有的 numpy），满足"不引入新依赖"约束。
6. 测试覆盖 4 个函数的正常路径、边界值（z=-1.0 green boundary、z=-2.0 yellow boundary）和错误输入（ValueError 路径），18 total 超出 12 下限。
7. `analyze_strategy_decay` 中 baseline 切片逻辑（`arr[:-recent_window]` 再调 `rolling_sharpe`）避免了 recent 与 baseline 数据重叠，设计正确。
8. 实现严格限定在 `quantpilot_stock.risk` 子包内，无"顺带重构"，无修改其他模块。

## 后续动作

PASS — PR 可合。本任务为 F.1.2，下游任务 F.1.3（VaR/CVaR）、F.1.4（API 路由）可直接消费本包内的纯函数。
