# Task phaseF8.dcf-api: DCF 估值 API 端点

**Phase**: Phase F.8
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/backend/src/quantpilot_stock/api/dcf.py`，注册到 `main.py`。

### 端点设计

```
GET /api/dcf/valuation?ticker=AAPL
    → DCFResult

GET /api/dcf/wacc?ticker=AAPL
    → WACCComponents
```

---

## 验收标准

- [ ] **AC-1**: 文件存在并注册
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/api/dcf.py`
  - `grep -q "dcf_router\|from.*dcf.*import" apps/stock-assistant/backend/src/quantpilot_stock/main.py`

- [ ] **AC-2**: 端点数量 ≥ 2
  - `grep -c "@router\." apps/stock-assistant/backend/src/quantpilot_stock/api/dcf.py`

- [ ] **AC-3**: 测试通过 (≥8)
  - `(cd apps/stock-assistant/backend && source ~/.zshrc 2>/dev/null && uv run pytest tests/test_dcf_api.py -v)` 退出码 0

- [ ] **AC-4**: mypy 通过
  - `(cd apps/stock-assistant/backend && source ~/.zshrc 2>/dev/null && uv run --isolated --with mypy python -m mypy src/quantpilot_stock/api/dcf.py)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/api/dcf.py`
- `apps/stock-assistant/backend/tests/test_dcf_api.py`

修改：
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`

> **批次开发说明**：F.8.1–F.8.3 在同一工作树批量开发并统一提交。
