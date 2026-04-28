# Task phaseF.risk-engine-core: Kelly Fraction + Vol Target 数学引擎

**Phase**: Phase F.1（风控三件套之 1）
**Status**: pending
**Implementation PR**: <pending>
**Created**: 2026-04-29
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

Brainstorm 决议（plan: `prompt-cached-sutherland.md` §2 Top-5 #5）落地的第 1 个子任务。此任务**只做最底层的数学引擎**：纯函数 + numpy/scipy，零外部 API、零 broker 依赖、零路由——为后续 `risk-sharpe-decay`、`risk-var-cvar`、`risk-api-endpoints` 共用。

### 做什么

新增 Python 子包 `quantpilot_stock.risk`，包含两个模块：

#### 1. `kelly.py` — Kelly Fraction 计算器

提供以下纯函数（全部带类型注解）：

- `kelly_fraction_binary(win_rate: float, payoff_ratio: float) -> float`
  - 经典 Kelly: `f* = p − q/b`，其中 `p` 胜率、`q=1−p`、`b` 赔率
  - 输入越界（`win_rate ∉ [0,1]` 或 `payoff_ratio <= 0`）→ raise `ValueError`
  - 计算结果 < 0（负 EV）→ 返回 0.0
- `kelly_fraction_from_returns(returns: np.ndarray) -> float`
  - 基于历史收益序列 r₁…rₙ 估算 Kelly：`f* ≈ μ / σ²`（连续近似 / Markowitz-Kelly）
  - `len(returns) < 10` → `ValueError`（样本太少）
  - `var(returns) == 0` → 返回 0.0
- `fractional_kelly(full_kelly: float, fraction: float = 0.25) -> float`
  - 实战版：把 full Kelly 乘 0.25（默认）做半保守仓位
  - `fraction` 必须 ∈ (0, 1]，否则 `ValueError`
- `capped_kelly(full_kelly: float, cap: float = 0.25) -> float`
  - 单只仓位上限（默认 25%）；负值截断到 0
  - 取 `min(max(full_kelly, 0.0), cap)`

#### 2. `vol_target.py` — Volatility Targeting 引擎

提供以下纯函数：

- `realized_volatility(returns: np.ndarray, *, annualize: bool = True, periods_per_year: int = 252) -> float`
  - 标准差 → 年化（√252 for daily）
  - `len(returns) < 2` → `ValueError`
- `vol_target_position_size(realized_vol: float, target_vol: float = 0.15) -> float`
  - 比例缩放：`size = target_vol / realized_vol`，capped at 1.0
  - `realized_vol <= 0` → `ValueError`；`target_vol <= 0` → `ValueError`
- `regime_classify(realized_vol: float, *, low_threshold: float = 0.10, high_threshold: float = 0.25) -> str`
  - 返回 `"low"` / `"normal"` / `"high"` / `"crisis"` 四档
  - `< low_threshold` → low；`< high_threshold` → normal；`< 2*high_threshold` → high；else crisis
- `vol_target_recommendation(returns: np.ndarray, target_vol: float = 0.15) -> dict[str, float | str]`
  - 一站式：返回 `{"realized_vol": ..., "regime": ..., "scale_factor": ..., "target_vol": ...}`

#### 3. 包初始化 `__init__.py`

re-export 上述 8 个公共名字。

### 不做什么

- **不做 API 路由**（留给 F.1.4）
- **不做前端**（留给 F.1.5）
- **不做 Sharpe 衰减监控**（留给 F.1.2）
- **不做 VaR/CVaR**（留给 F.1.3）
- **不引入新依赖**（numpy 已有，不要装新包）
- **不改 `common/`**（数学引擎放在 stock-assistant 内部即可，未来证明跨 app 复用再上移）
- **不写 docstring 长篇大论**（短一行 + Args/Returns 必要时）

---

## 验收标准（acceptance-agent 逐条核对）

- [ ] **AC-1**: 模块文件存在
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/risk/__init__.py`
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/risk/kelly.py`
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/risk/vol_target.py`
- [ ] **AC-2**: 测试文件存在
  - `test -f apps/stock-assistant/backend/tests/test_risk_kelly_vol.py`
- [ ] **AC-3**: 全部 8 个公共函数可从顶包 import
  - `(cd apps/stock-assistant/backend && uv run python -c "from quantpilot_stock.risk import kelly_fraction_binary, kelly_fraction_from_returns, fractional_kelly, capped_kelly, realized_volatility, vol_target_position_size, regime_classify, vol_target_recommendation")` 退出码 0
- [ ] **AC-4**: 单测全过
  - `(cd apps/stock-assistant/backend && uv run pytest tests/test_risk_kelly_vol.py -v)` 退出码 0
  - 单测数 ≥ 18（覆盖每个函数 ≥ 2 个用例）
- [ ] **AC-5**: ruff 干净
  - `(cd apps/stock-assistant/backend && uv run --with ruff ruff check src/quantpilot_stock/risk/ tests/test_risk_kelly_vol.py)` 退出码 0
- [ ] **AC-6**: mypy 干净
  - `(cd apps/stock-assistant/backend && uv run --with mypy mypy src/quantpilot_stock/risk/ --ignore-missing-imports)` 退出码 0，输出含 `Success: no issues found`
- [ ] **AC-7**: 不引入新依赖
  - `git diff main -- apps/stock-assistant/backend/pyproject.toml` 输出为空（dependencies 未改）
- [ ] **AC-8**: 不修改其它 app
  - `! git diff main -- apps/quant-assistant/ common/ | grep -q "^[-+]"`（除 docs 外应无改动）
- [ ] **AC-9**: 现有测试无回归
  - `(cd apps/stock-assistant/backend && uv run pytest tests/ -x --ignore=tests/test_risk_kelly_vol.py -q)` 退出码 0

---

## 测试集合（acceptance-agent 必跑）

```bash
# 1. 单测全过
(cd apps/stock-assistant/backend && uv run pytest tests/test_risk_kelly_vol.py -v)

# 2. ruff
(cd apps/stock-assistant/backend && uv run --with ruff ruff check src/quantpilot_stock/risk/ tests/test_risk_kelly_vol.py)

# 3. mypy
(cd apps/stock-assistant/backend && uv run --with mypy mypy src/quantpilot_stock/risk/ --ignore-missing-imports)

# 4. import 烟雾测试
(cd apps/stock-assistant/backend && uv run python -c "from quantpilot_stock.risk import kelly_fraction_binary, kelly_fraction_from_returns, fractional_kelly, capped_kelly, realized_volatility, vol_target_position_size, regime_classify, vol_target_recommendation; print('ok')")

# 5. 现有测试不回归
(cd apps/stock-assistant/backend && uv run pytest tests/ -x --ignore=tests/test_risk_kelly_vol.py -q)

# 6. pyproject.toml 未改
git diff main -- apps/stock-assistant/backend/pyproject.toml
```

---

## 文件影响范围（白名单）

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/risk/__init__.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/risk/kelly.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/risk/vol_target.py`
- `apps/stock-assistant/backend/tests/test_risk_kelly_vol.py`
- `docs/tasks/phaseF/README.md`（已建）
- `docs/tasks/phaseF/risk-engine-core.md`（本 spec）

不允许改：
- 所有其它 `apps/`、`common/`、`tools/` 路径
- 所有 `pyproject.toml` / `uv.lock`

---

## 引用

- **设计来源**：plan `prompt-cached-sutherland.md` §2 Top-5 #5（Kelly + Vol Target + 衰减预警 + 尾部风险）
- **上游依赖**：无
- **下游依赖**：F.1.2 / F.1.3 / F.1.4 都会消费本任务定义的纯函数
- **相关文档**：`docs/tasks/phaseF/README.md`、CLAUDE.md
