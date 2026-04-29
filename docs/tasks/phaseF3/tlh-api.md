# Task phaseF3.tlh-api: TLH API 端点

**Phase**: Phase F.3
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/backend/src/quantpilot_stock/api/tlh.py`，注册到 `main.py`。

### 端点设计

```
POST /api/tlh/scan
    Body: { lots: [{ticker, quantity, cost_basis, acquisition_date, lot_id}],
            current_prices: {ticker: price},
            recent_purchases: {ticker: "YYYY-MM-DD"} }
    → { candidates: [...], estimated_tax_saving, generated_at }

GET /api/tlh/replacement?ticker=SPY
    → { ticker, replacements: ["VOO", "IVV", ...] }

POST /api/tlh/estimate-saving
    Body: { candidates: [...], short_term_rate, long_term_rate }
    → { tax_saving_usd, details: [...] }
```

---

## 验收标准

- [ ] **AC-1**: 文件存在并注册
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/api/tlh.py`
  - `grep -q "tlh_router\|from.*tlh.*import" apps/stock-assistant/backend/src/quantpilot_stock/main.py`

- [ ] **AC-2**: 端点数量
  - `grep -c "@router\." apps/stock-assistant/backend/src/quantpilot_stock/api/tlh.py` 输出 ≥ 3

- [ ] **AC-3**: 测试通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run pytest tests/test_tlh_api.py -v)` 退出码 0
  - 至少 8 个测试

- [ ] **AC-4**: mypy 通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run --isolated --with mypy python -m mypy src/quantpilot_stock/api/tlh.py)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/api/tlh.py`
- `apps/stock-assistant/backend/tests/test_tlh_api.py`

修改：
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`

> **批次开发说明**：F.3.1–F.3.5 在同一工作树批量开发并统一提交。验收时须在 clean working tree（`git diff HEAD` 为空）下执行。
