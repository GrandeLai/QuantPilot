# Acceptance Report: phaseF.crypto-basis-engine

**Run at**: 2026-04-28T00:00:00Z
**Implementation commit**: `59a18c4`
**Diff range**: `59a18c4^..59a18c4`
**Acceptance-agent invocation**: v1
**Verdict**: PASS

## 文件影响范围检查

- 改动文件总数：4
- 在白名单内：4
- 超出白名单：0

明细：
- `apps/stock-assistant/backend/src/quantpilot_stock/crypto_derivs/analytics.py` — 白名单（新建）
- `apps/stock-assistant/backend/src/quantpilot_stock/crypto_derivs/__init__.py` — 白名单（修改，追加 4 个 export）
- `apps/stock-assistant/backend/tests/test_crypto_derivs_analytics.py` — 白名单（新建）
- `docs/tasks/phaseF/crypto-basis-engine.md` — 白名单（本 spec）

`pyproject.toml` 未出现在 diff 中，满足"不允许改"约束。

## 验收标准核对

| AC | 状态 | 证据 |
|---|---|---|
| AC-1: 两个文件存在 | ✅ PASS | `test -f analytics.py` 和 `test -f test_crypto_derivs_analytics.py` 均返回 0 |
| AC-2: 4 个新函数可从子包顶层 import | ✅ PASS | `uv run python -c "from quantpilot_stock.crypto_derivs import compute_basis, funding_percentile_stats, funding_extreme_signal, oi_momentum, fetch_aggregated_derivs; print('ok')"` 输出 `ok`，退出码 0 |
| AC-3: 单测全过，用例数 ≥ 12 | ✅ PASS | 19 collected, 19 passed in 0.37s，退出码 0；远超 ≥ 12 下限 |
| AC-4: ruff 干净 | ✅ PASS | `All checks passed!`，退出码 0 |
| AC-5: mypy 干净 | ✅ PASS | `Success: no issues found in 4 source files`，退出码 0 |
| AC-6: pyproject.toml 未改 | ✅ PASS | `git diff main -- .../pyproject.toml` 无输出，退出码 0 |
| AC-7: 现有测试无回归 | ✅ PASS | 264 passed in 7.43s，退出码 0（--ignore=test_crypto_derivs_analytics.py） |
| AC-8: F.1.10 collector 导出未破坏 | ✅ PASS | `from quantpilot_stock.crypto_derivs import fetch_aggregated_derivs, FundingRate, OpenInterest` 退出码 0（与 AC-2 同一命令覆盖） |

## 测试执行日志摘要

### 1. 单测全过（AC-3）
```
pytest tests/test_crypto_derivs_analytics.py -v
19 collected, 19 passed in 0.37s
EXIT: 0
```

### 2. ruff（AC-4）
```
uv run --with ruff ruff check src/quantpilot_stock/crypto_derivs/ tests/test_crypto_derivs_analytics.py
All checks passed!
EXIT: 0
```

### 3. mypy（AC-5）
```
uv run --with mypy mypy src/quantpilot_stock/crypto_derivs/ --ignore-missing-imports
Success: no issues found in 4 source files
EXIT: 0
```

### 4. import 烟雾测试（AC-2 + AC-8）
```
uv run python -c "from quantpilot_stock.crypto_derivs import compute_basis, funding_percentile_stats, funding_extreme_signal, oi_momentum, fetch_aggregated_derivs; print('ok')"
ok
EXIT: 0
```

### 5. 现有测试无回归（AC-7）
```
pytest tests/ -x --ignore=tests/test_crypto_derivs_analytics.py -q
264 passed in 7.43s
EXIT: 0
```

### 6. pyproject.toml 未改（AC-6）
```
git diff main -- apps/stock-assistant/backend/pyproject.toml
(no output)
EXIT: 0
```

## 代码 Review 备注

1. `analytics.py` 有模块级 docstring，符合 CLAUDE.md Python 规范。
2. 所有 4 个公共函数均有完整 type hints 和 docstring（Args + Returns 均注释）。
3. 无跨 app import：`analytics.py` 仅依赖标准库 `typing` 和 `numpy`（已有依赖），不引入任何新第三方包。
4. `__init__.py` 更新仅追加 4 个新符号，原有 collector/models 导出完整保留，backward compatible。
5. `oi_momentum` 对 `current_oi < 0` 和 `prior_oi <= 0` 都有 ValueError 保护，符合 spec "prior 为 0 → ValueError"。
6. `funding_extreme_signal` 对 sigma=0 场景以 `z_score=0.0` 返回 neutral（而非 ZeroDivisionError），实现合理。
7. 测试文件有模块级 docstring，19 个用例覆盖所有 4 个函数的 happy path + 边界（负价格、样本不足、零方差、自定义阈值、零 prior OI、负 current OI），质量高。
8. 实现严格限定在 `quantpilot_stock.crypto_derivs` 子包内，无"顺带重构"。
9. 接口设计与 spec 完全一致：返回 dict 键名均与 spec 所列匹配；`fundings_per_year` 默认值 1095 正确。

## 后续动作

PASS — PR 可合。本任务为纯静态分析层，下游任务 F.1.13（前端面板）可直接调用 `compute_basis`、`funding_percentile_stats`、`funding_extreme_signal`、`oi_momentum` 四个函数构建实时面板。
