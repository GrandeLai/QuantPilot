# Task phaseF.crypto-basis-engine: Spot-Perp Basis + Funding 统计引擎

**Phase**: Phase F.1（加密衍生品面板之 2）
**Status**: pending
**Implementation PR**: <pending>
**Created**: 2026-04-29
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

F.1.10 已实现 funding/OI 数据采集。本任务在 collector 之上增加**纯数学引擎**：
- Spot-Perp basis 计算 + cash-and-carry 年化 yield 估算
- funding rate 历史统计：百分位带、z-score、极值检测（反向信号）

零外部 API、纯 Python，类似风控三件套的 F.1.1 做法。下游 F.1.13 (前端) 消费。

### 做什么

新增模块 `quantpilot_stock.crypto_derivs.analytics`：

#### 1. `compute_basis(spot_price, perp_price, funding_rate, *, fundings_per_year=1095) -> dict`

```
basis_abs = perp_price - spot_price
basis_bps = (basis_abs / spot_price) * 10_000
# 年化 cash-and-carry yield = funding_rate × fundings_per_year
funding_apr = funding_rate * fundings_per_year   # 默认 1095 ≈ 365×3 (8h funding)
```

返回 dict: `{spot_price, perp_price, basis_abs, basis_bps, funding_rate, funding_apr}`。

#### 2. `funding_percentile_stats(history: list[float]) -> dict`

输入：funding rate 历史序列（≥ 30 个样本，否则 ValueError）。
输出：
- mean, std
- p5, p25, p50, p75, p95
- current is **None** here（caller 自己拿）

#### 3. `funding_extreme_signal(current_funding: float, history: list[float], *, z_threshold: float = 2.0) -> dict`

判断当前 funding 是否极值反向信号。返回：
- `z_score`：(current - mean) / std
- `signal`: `"contrarian_short"` (z >= z_threshold), `"contrarian_long"` (z <= -z_threshold), `"neutral"` 其它
- `percentile`: 当前在历史中的百分位（0-100）

样本不足 → ValueError。

#### 4. `oi_momentum(current_oi: float, prior_oi: float) -> dict`

```
oi_change_pct = (current - prior) / prior × 100
```

返回 `{current_oi, prior_oi, oi_change_pct, direction: "up"|"down"|"flat"}`。
prior 为 0 → ValueError。

#### 5. 包导出

更新 `crypto_derivs/__init__.py` re-export 4 个新函数。

#### 6. 测试 `tests/test_crypto_derivs_analytics.py`

≥ 12 用例，覆盖每函数 happy path + 边界。

### 不做什么

- 不接 collector（caller 自己组装）；本层是纯静态分析
- 不做 ETF flow（F.1.12）
- 不做 API / 前端
- 不引入新依赖

---

## 验收标准

- [ ] **AC-1**: 文件存在
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/crypto_derivs/analytics.py`
  - `test -f apps/stock-assistant/backend/tests/test_crypto_derivs_analytics.py`
- [ ] **AC-2**: 4 个新函数可从子包顶层 import
  - `(cd apps/stock-assistant/backend && uv run python -c "from quantpilot_stock.crypto_derivs import compute_basis, funding_percentile_stats, funding_extreme_signal, oi_momentum")` 退出码 0
- [ ] **AC-3**: 单测全过 — `(cd apps/stock-assistant/backend && uv run pytest tests/test_crypto_derivs_analytics.py -v)` 退出码 0；用例数 ≥ 12
- [ ] **AC-4**: ruff 干净 — `(cd apps/stock-assistant/backend && uv run --with ruff ruff check src/quantpilot_stock/crypto_derivs/ tests/test_crypto_derivs_analytics.py)`
- [ ] **AC-5**: mypy 干净 — `(cd apps/stock-assistant/backend && uv run --with mypy mypy src/quantpilot_stock/crypto_derivs/ --ignore-missing-imports)`
- [ ] **AC-6**: 不引入新依赖 — `git diff main -- apps/stock-assistant/backend/pyproject.toml` 输出为空
- [ ] **AC-7**: 现有测试无回归 — `(cd apps/stock-assistant/backend && uv run pytest tests/ -x --ignore=tests/test_crypto_derivs_analytics.py -q)` 退出码 0
- [ ] **AC-8**: F.1.10 collector 导出未破坏 — `(cd apps/stock-assistant/backend && uv run python -c "from quantpilot_stock.crypto_derivs import fetch_aggregated_derivs, FundingRate, OpenInterest")` 退出码 0

---

## 测试集合

```bash
(cd apps/stock-assistant/backend && uv run pytest tests/test_crypto_derivs_analytics.py -v)
(cd apps/stock-assistant/backend && uv run --with ruff ruff check src/quantpilot_stock/crypto_derivs/ tests/test_crypto_derivs_analytics.py)
(cd apps/stock-assistant/backend && uv run --with mypy mypy src/quantpilot_stock/crypto_derivs/ --ignore-missing-imports)
(cd apps/stock-assistant/backend && uv run python -c "from quantpilot_stock.crypto_derivs import compute_basis, funding_percentile_stats, funding_extreme_signal, oi_momentum, fetch_aggregated_derivs; print('ok')")
(cd apps/stock-assistant/backend && uv run pytest tests/ -x --ignore=tests/test_crypto_derivs_analytics.py -q)
git diff main -- apps/stock-assistant/backend/pyproject.toml
```

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/crypto_derivs/analytics.py`
- `apps/stock-assistant/backend/tests/test_crypto_derivs_analytics.py`
- `docs/tasks/phaseF/crypto-basis-engine.md`

修改：
- `apps/stock-assistant/backend/src/quantpilot_stock/crypto_derivs/__init__.py`（追加 4 个 export）

不允许改：所有其它路径。

---

## 引用

- **设计来源**：plan §2 Top-5 #2；F.1 README
- **上游依赖**：F.1.10
- **下游依赖**：F.1.13（前端面板调用）
