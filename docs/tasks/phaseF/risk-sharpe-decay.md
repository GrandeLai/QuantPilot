# Task phaseF.risk-sharpe-decay: 滚动 Sharpe 衰减预警

**Phase**: Phase F.1（风控三件套之 2）
**Status**: pending
**Implementation PR**: <pending>
**Created**: 2026-04-29
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

紧跟 F.1.1（Kelly + Vol Target 数学引擎）。本任务实现「策略 Sharpe 衰减监控」——给定一条策略的历史收益序列，输出滚动 Sharpe 曲线 + 与历史分布的 z-score + 黄/红牌告警，避免"策略已死还在加仓"的灾难。

### 做什么

新增模块 `quantpilot_stock.risk.sharpe_decay`，提供：

- `rolling_sharpe(returns: np.ndarray, *, window: int = 63, periods_per_year: int = 252) -> np.ndarray`
  - 滚动窗口 Sharpe，默认 63 个交易日（约 3 月）
  - 返回长度同输入、前 `window-1` 个为 NaN
  - `window < 10` → ValueError；`len(returns) < window` → ValueError
- `sharpe_z_score(current_sharpe: float, baseline: np.ndarray) -> float`
  - 当前 Sharpe 相对历史分布的 z-score：`(current - mean) / std`
  - `len(baseline) < 10` → ValueError
  - baseline std 为 0 → 返回 0.0
- `decay_alert_level(z_score: float) -> Literal["green", "yellow", "red"]`
  - z >= -1 → "green"
  - -2 <= z < -1 → "yellow"（衰减预警）
  - z < -2 → "red"（应下架/降权）
- `analyze_strategy_decay(returns: np.ndarray, *, recent_window: int = 63, baseline_window: int = 252) -> dict[str, float | str | int]`
  - 一站式：返回 `{recent_sharpe, baseline_mean, baseline_std, z_score, alert_level, n_baseline_samples}`
  - 至少需要 `recent_window + baseline_window + 10` 个样本，否则 ValueError
- 更新 `risk/__init__.py` 导出上述 4 个新函数

### 不做什么

- 不引入 pandas（保持 numpy-only）
- 不做 API 路由（留 F.1.4）
- 不做前端（留 F.1.5）
- 不引入新依赖

---

## 验收标准

- [ ] **AC-1**: `test -f apps/stock-assistant/backend/src/quantpilot_stock/risk/sharpe_decay.py`
- [ ] **AC-2**: `test -f apps/stock-assistant/backend/tests/test_risk_sharpe_decay.py`
- [ ] **AC-3**: 4 个新函数可从顶包 import — `(cd apps/stock-assistant/backend && uv run python -c "from quantpilot_stock.risk import rolling_sharpe, sharpe_z_score, decay_alert_level, analyze_strategy_decay")` 退出码 0
- [ ] **AC-4**: 单测全过 — `(cd apps/stock-assistant/backend && uv run pytest tests/test_risk_sharpe_decay.py -v)` 退出码 0；用例数 ≥ 12
- [ ] **AC-5**: ruff 干净 — `(cd apps/stock-assistant/backend && uv run --with ruff ruff check src/quantpilot_stock/risk/ tests/test_risk_sharpe_decay.py)`
- [ ] **AC-6**: mypy 干净 — `(cd apps/stock-assistant/backend && uv run --with mypy mypy src/quantpilot_stock/risk/ --ignore-missing-imports)`
- [ ] **AC-7**: 不引入新依赖 — `git diff main -- apps/stock-assistant/backend/pyproject.toml` 输出为空
- [ ] **AC-8**: 现有测试无回归 — `(cd apps/stock-assistant/backend && uv run pytest tests/ -x --ignore=tests/test_risk_sharpe_decay.py -q)` 退出码 0
- [ ] **AC-9**: F.1.1 的导出未破坏 — `(cd apps/stock-assistant/backend && uv run python -c "from quantpilot_stock.risk import kelly_fraction_binary, vol_target_recommendation")` 退出码 0

---

## 测试集合

```bash
(cd apps/stock-assistant/backend && uv run pytest tests/test_risk_sharpe_decay.py -v)
(cd apps/stock-assistant/backend && uv run --with ruff ruff check src/quantpilot_stock/risk/ tests/test_risk_sharpe_decay.py)
(cd apps/stock-assistant/backend && uv run --with mypy mypy src/quantpilot_stock/risk/ --ignore-missing-imports)
(cd apps/stock-assistant/backend && uv run python -c "from quantpilot_stock.risk import rolling_sharpe, sharpe_z_score, decay_alert_level, analyze_strategy_decay; print('ok')")
(cd apps/stock-assistant/backend && uv run pytest tests/ -x --ignore=tests/test_risk_sharpe_decay.py -q)
git diff main -- apps/stock-assistant/backend/pyproject.toml
```

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/risk/sharpe_decay.py`
- `apps/stock-assistant/backend/tests/test_risk_sharpe_decay.py`
- `docs/tasks/phaseF/risk-sharpe-decay.md`（本 spec）

修改：
- `apps/stock-assistant/backend/src/quantpilot_stock/risk/__init__.py`（追加 4 个 export）

不允许改：所有其它路径。

---

## 引用

- **设计来源**：plan §2 Top-5 #5；F.1 README
- **上游依赖**：F.1.1（risk-engine-core）— 共用 `risk/__init__.py`
- **下游依赖**：F.1.4（risk-api-endpoints）将暴露此能力
