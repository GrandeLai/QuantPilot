# Task phaseF.risk-api-endpoints: Risk Engine HTTP API

**Phase**: Phase F.1
**Status**: pending
**Implementation PR**: <pending>
**Created**: 2026-04-29
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

F.1.1/1.2/1.3 已交付纯 Python 风控引擎（kelly + vol_target + sharpe_decay + var_cvar）。本任务把它暴露成 HTTP API，前端 F.1.5 将消费这些端点。同时通过 `/api` alias 以匹配项目的统一前缀习惯。

### 做什么

新增 `apps/stock-assistant/backend/src/quantpilot_stock/api/risk.py`，定义 5 个端点：

#### 1. `POST /risk/kelly`

Body：
```json
{
  "mode": "binary" | "returns",
  "win_rate": 0.55,         // mode=binary
  "payoff_ratio": 1.5,       // mode=binary
  "returns": [0.01, ...],    // mode=returns
  "fraction": 0.25,          // 可选：fractional Kelly
  "cap": 0.25                // 可选：单只上限
}
```

Response：
```json
{
  "full_kelly": 0.25,
  "fractional_kelly": 0.0625,
  "capped_kelly": 0.0625,
  "mode": "binary"
}
```

#### 2. `POST /risk/vol-target`

Body：`{"returns": [...], "target_vol": 0.15}` → 返回 `vol_target_recommendation` 结果

#### 3. `POST /risk/sharpe-decay`

Body：`{"returns": [...], "recent_window": 63, "baseline_window": 252}` → 返回 `analyze_strategy_decay` 结果

#### 4. `POST /risk/var`

Body：
```json
{
  "returns": [...],
  "confidences": [0.95, 0.99],
  "method": "historical" | "parametric" | "both"
}
```

Response：`var_summary` 直出

#### 5. `POST /risk/summary`

一站式：把 vol_target + sharpe_decay + var 合一调用，返回组合 dict（`vol_target`、`sharpe_decay`、`var`、`n_samples`）。

#### 6. 在 `main.py` 注册 router

按 `include_with_api_alias` 模式注册，与 insights/portfolio 等并列。

#### 7. 测试 `tests/test_risk_api.py`

用 FastAPI TestClient 跑每个端点的 happy path + 至少一个错误路径（缺字段、样本太少）。≥ 12 用例。

### 不做什么

- 不做 GET 缓存端点（数据短小，POST 即可）
- 不做权限/JWT
- 不做 WebSocket
- 不引入新依赖

### 错误处理

- Pydantic 校验 → 422 自动返回
- 引擎层 `ValueError`（样本不足、参数越界）→ 在端点 try/except 包成 `HTTPException(400, detail=str(e))`

---

## 验收标准

- [ ] **AC-1**: `test -f apps/stock-assistant/backend/src/quantpilot_stock/api/risk.py`
- [ ] **AC-2**: `test -f apps/stock-assistant/backend/tests/test_risk_api.py`
- [ ] **AC-3**: `grep -q "from quantpilot_stock.api.risk import router as risk_router" apps/stock-assistant/backend/src/quantpilot_stock/main.py` 退出码 0
- [ ] **AC-4**: `grep -q "include_with_api_alias(risk_router)" apps/stock-assistant/backend/src/quantpilot_stock/main.py` 退出码 0
- [ ] **AC-5**: 单测全过 — `(cd apps/stock-assistant/backend && uv run pytest tests/test_risk_api.py -v)` 退出码 0；用例数 ≥ 12
- [ ] **AC-6**: ruff 干净 — `(cd apps/stock-assistant/backend && uv run --with ruff ruff check src/quantpilot_stock/api/risk.py tests/test_risk_api.py src/quantpilot_stock/main.py)`
- [ ] **AC-7**: mypy 干净 — `(cd apps/stock-assistant/backend && uv run --with mypy mypy src/quantpilot_stock/api/risk.py --ignore-missing-imports)`
- [ ] **AC-8**: 不引入新依赖 — `git diff main -- apps/stock-assistant/backend/pyproject.toml` 输出为空
- [ ] **AC-9**: 现有测试无回归 — `(cd apps/stock-assistant/backend && uv run pytest tests/ -x --ignore=tests/test_risk_api.py -q)` 退出码 0
- [ ] **AC-10**: 端点真实可用 — 启动 app 后 `POST /api/risk/kelly` 返回 200（用 TestClient 在测试中验证即可）

---

## 测试集合

```bash
(cd apps/stock-assistant/backend && uv run pytest tests/test_risk_api.py -v)
(cd apps/stock-assistant/backend && uv run --with ruff ruff check src/quantpilot_stock/api/risk.py tests/test_risk_api.py src/quantpilot_stock/main.py)
(cd apps/stock-assistant/backend && uv run --with mypy mypy src/quantpilot_stock/api/risk.py --ignore-missing-imports)
(cd apps/stock-assistant/backend && uv run pytest tests/ -x --ignore=tests/test_risk_api.py -q)
git diff main -- apps/stock-assistant/backend/pyproject.toml
grep -n "risk_router\|risk\.py" apps/stock-assistant/backend/src/quantpilot_stock/main.py
```

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/api/risk.py`
- `apps/stock-assistant/backend/tests/test_risk_api.py`
- `docs/tasks/phaseF/risk-api-endpoints.md`

修改：
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`（注册 risk_router 一处 import + 一处 include_with_api_alias）

不允许改：所有其它路径。

---

## 引用

- **设计来源**：plan §2 Top-5 #5；F.1 README
- **上游依赖**：F.1.1 / F.1.2 / F.1.3 风控引擎
- **下游依赖**：F.1.5 前端 RiskMetricsPanel 消费这些端点
