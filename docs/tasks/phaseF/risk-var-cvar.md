# Task phaseF.risk-var-cvar: 历史 VaR / CVaR 引擎

**Phase**: Phase F.1（风控三件套之 3）
**Status**: pending
**Implementation PR**: <pending>
**Created**: 2026-04-29
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

风控三件套最后一块：组合层尾部风险。提供 Historical VaR、Historical CVaR (Expected Shortfall)、Parametric VaR (Gaussian) 三种估算方式，以及一站式 `var_summary` 输出多个置信度。EVT 高级方法留到完整版（不在 MVP 范围）。

### 做什么

新增模块 `quantpilot_stock.risk.var_cvar`：

- `historical_var(returns: np.ndarray, *, confidence: float = 0.95) -> float`
  - 返回**正数**——表示给定置信水平下的最大损失（亏损绝对值）
  - 用 `np.quantile(returns, 1 - confidence)`，再取 max(-q, 0.0)
  - `confidence ∉ (0, 1)` 或 `len(returns) < 30` → ValueError
- `historical_cvar(returns: np.ndarray, *, confidence: float = 0.95) -> float`
  - Expected Shortfall：尾部均值（同样返回正数）
  - 取 `returns[returns <= quantile]` 的均值，再取负值
  - 与 `historical_var` 同样的输入校验
- `parametric_var(returns: np.ndarray, *, confidence: float = 0.95) -> float`
  - 高斯参数法：`var = -(μ + z * σ)`，z 用 `scipy.stats.norm.ppf(1 - confidence)`
  - clipped 到 ≥ 0（极少数情况均值大到把 var 推为负）
- `var_summary(returns: np.ndarray, *, confidences: tuple[float, ...] = (0.95, 0.99), method: Literal["historical", "parametric", "both"] = "historical") -> dict[str, float | str | int]`
  - 一站式：返回各置信度的 var/cvar，同时给样本数和最差观测亏损
  - keys: `n_samples`, `worst_loss`, `var_95`, `var_99`, `cvar_95`, `cvar_99`（以及 method 为 both 时的 `parametric_var_95`, `parametric_var_99`）
- 更新 `risk/__init__.py` 导出上述 4 个新函数

### 不做什么

- 不做 EVT (Peaks-Over-Threshold)、不做 Cornish-Fisher 修正、不做 Monte Carlo VaR（留到完整版）
- 不做 vol skew radar（独立任务，未排进此批）
- 不引入 pandas
- 不做 API 路由（F.1.4）/ 前端（F.1.5）

---

## 验收标准

- [ ] **AC-1**: `test -f apps/stock-assistant/backend/src/quantpilot_stock/risk/var_cvar.py`
- [ ] **AC-2**: `test -f apps/stock-assistant/backend/tests/test_risk_var_cvar.py`
- [ ] **AC-3**: 4 个新函数可从顶包 import — `(cd apps/stock-assistant/backend && uv run python -c "from quantpilot_stock.risk import historical_var, historical_cvar, parametric_var, var_summary")` 退出码 0
- [ ] **AC-4**: 单测全过 — `(cd apps/stock-assistant/backend && uv run pytest tests/test_risk_var_cvar.py -v)` 退出码 0；用例数 ≥ 14
- [ ] **AC-5**: ruff 干净 — `(cd apps/stock-assistant/backend && uv run --with ruff ruff check src/quantpilot_stock/risk/ tests/test_risk_var_cvar.py)`
- [ ] **AC-6**: mypy 干净 — `(cd apps/stock-assistant/backend && uv run --with mypy mypy src/quantpilot_stock/risk/ --ignore-missing-imports)`
- [ ] **AC-7**: 不引入新依赖 — `git diff main -- apps/stock-assistant/backend/pyproject.toml` 输出为空
- [ ] **AC-8**: 现有测试无回归 — `(cd apps/stock-assistant/backend && uv run pytest tests/ -x --ignore=tests/test_risk_var_cvar.py -q)` 退出码 0
- [ ] **AC-9**: 之前任务的导出未破坏 — `(cd apps/stock-assistant/backend && uv run python -c "from quantpilot_stock.risk import kelly_fraction_binary, vol_target_recommendation, analyze_strategy_decay")` 退出码 0

---

## 测试集合

```bash
(cd apps/stock-assistant/backend && uv run pytest tests/test_risk_var_cvar.py -v)
(cd apps/stock-assistant/backend && uv run --with ruff ruff check src/quantpilot_stock/risk/ tests/test_risk_var_cvar.py)
(cd apps/stock-assistant/backend && uv run --with mypy mypy src/quantpilot_stock/risk/ --ignore-missing-imports)
(cd apps/stock-assistant/backend && uv run python -c "from quantpilot_stock.risk import historical_var, historical_cvar, parametric_var, var_summary; print('ok')")
(cd apps/stock-assistant/backend && uv run pytest tests/ -x --ignore=tests/test_risk_var_cvar.py -q)
git diff main -- apps/stock-assistant/backend/pyproject.toml
```

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/risk/var_cvar.py`
- `apps/stock-assistant/backend/tests/test_risk_var_cvar.py`
- `docs/tasks/phaseF/risk-var-cvar.md`

修改：
- `apps/stock-assistant/backend/src/quantpilot_stock/risk/__init__.py`（追加 4 个 export）

捎带（type-c：并行进程污染工作树，已在白名单事后追认）：
- `docs/Claude_Code_Usage_Guide.md` → `docs/archive/legacy/Claude_Code_Usage_Guide.md` (R100)
- `docs/factor_guide.md` → `docs/archive/legacy/factor_guide.md` (R100)
- `docs/llm-agent-layer-design.md` → `docs/archive/legacy/llm-agent-layer-design.md` (R100)
- `docs/tab-pages-guide.md` → `docs/archive/legacy/tab-pages-guide.md` (R100)
  - 原因：另一会话在我开干前已 partial-stage 这 4 个 rename，未提交。我 `git add` 时被 git mv 检测合并进了 stage。零内容改动（R100），属于并行的 phaseE.docs-cleanup-refresh 任务范围（详见 commit 854ebfb / e59a73d）。
  - 教训：每个新 task 开干前必须 `git status` 确认工作树干净，已记入流程改进。

不允许改：除以上之外的所有路径。

---

## 引用

- **设计来源**：plan §2 Top-5 #5；F.1 README
- **上游依赖**：F.1.1（risk-engine-core）、F.1.2（risk-sharpe-decay）共用 `risk/__init__.py`
- **下游依赖**：F.1.4（risk-api-endpoints）暴露此能力
