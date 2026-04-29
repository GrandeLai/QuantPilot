# Task phaseF4.fundamental-api: 基本面信号 API 端点

**Phase**: Phase F.4
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/backend/src/quantpilot_stock/api/fundamental.py`，注册到 `main.py`。

### 端点设计

```
GET /api/fundamental/pead?ticker=AAPL
    → PEADSignal（最新 EPS surprise + 历史漂移估算）

GET /api/fundamental/piotroski?ticker=AAPL
    → PiotroskiScore（9 维评分 + 明细）

GET /api/fundamental/summary?ticker=AAPL
    → { pead: PEADSignal | None, piotroski: PiotroskiScore | None }
```

---

## 验收标准

- [ ] **AC-1**: 文件存在并注册
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/api/fundamental.py`
  - `grep -q "fundamental_router\|from.*fundamental.*import" apps/stock-assistant/backend/src/quantpilot_stock/main.py`

- [ ] **AC-2**: 端点数量
  - `grep -c "@router\." apps/stock-assistant/backend/src/quantpilot_stock/api/fundamental.py` 输出 ≥ 3

- [ ] **AC-3**: 测试通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run pytest tests/test_fundamental_api.py -v)` 退出码 0
  - 至少 8 个测试

- [ ] **AC-4**: mypy 通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run --isolated --with mypy python -m mypy src/quantpilot_stock/api/fundamental.py)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/api/fundamental.py`
- `apps/stock-assistant/backend/tests/test_fundamental_api.py`

修改：
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`

> **批次开发说明**：F.4.1–F.4.3 在同一工作树批量开发并统一提交。
