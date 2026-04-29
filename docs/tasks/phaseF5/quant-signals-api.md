# Task phaseF5.quant-signals-api: 量化信号 API 端点

**Phase**: Phase F.5
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/backend/src/quantpilot_stock/api/quant_signals.py`，注册到 `main.py`。

### 端点设计

```
GET /api/quant-signals/beneish?ticker=AAPL
    → BeneishMScore

GET /api/quant-signals/russell?ticker=AAPL
    → RussellMembership

GET /api/quant-signals/summary?ticker=AAPL
    → { beneish: BeneishMScore | None, russell: RussellMembership | None }
```

---

## 验收标准

- [ ] **AC-1**: 文件存在并注册
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/api/quant_signals.py`
  - `grep -q "quant_signals_router\|from.*quant_signals.*import" apps/stock-assistant/backend/src/quantpilot_stock/main.py`

- [ ] **AC-2**: 端点数量
  - `grep -c "@router\." apps/stock-assistant/backend/src/quantpilot_stock/api/quant_signals.py` 输出 ≥ 3

- [ ] **AC-3**: 测试通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run pytest tests/test_quant_signals_api.py -v)` 退出码 0
  - 至少 8 个测试

- [ ] **AC-4**: mypy 通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run --isolated --with mypy python -m mypy src/quantpilot_stock/api/quant_signals.py)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/api/quant_signals.py`
- `apps/stock-assistant/backend/tests/test_quant_signals_api.py`

修改：
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`

> **批次开发说明**：F.5.1–F.5.3 在同一工作树批量开发并统一提交。
