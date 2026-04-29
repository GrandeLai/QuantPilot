# Task phaseF3.execution-api: TWAP/VWAP/TCA API 端点

**Phase**: Phase F.3
**Status**: pending
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/backend/src/quantpilot_stock/api/execution.py`，注册到 `main.py`。

### 端点设计

```
POST /api/execution/twap
    Body: { ticker, total_quantity, start_time, end_time,
            num_slices?, time_interval_minutes? }
    → ExecutionReport（ChildOrder 列表 + 参数）

POST /api/execution/vwap
    Body: { ticker, total_quantity, start_time, end_time,
            volume_profile?, num_slices? }
    → ExecutionReport

POST /api/execution/tca
    Body: { ticker, arrival_price, executed_avg_price,
            vwap_price?, close_price?, total_quantity,
            algo, parent_order_id?, execution_date? }
    → TCARecord（slippage_bps + 各基准偏离）

GET /api/execution/adv-check?ticker=AAPL&quantity=10000&adv=200000
    → { needs_slicing: bool, recommended_slices: int, threshold_pct: float }
```

---

## 验收标准

- [ ] **AC-1**: 文件存在并注册
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/api/execution.py`
  - `grep -q "execution_router\|from.*execution.*import" apps/stock-assistant/backend/src/quantpilot_stock/main.py`

- [ ] **AC-2**: 端点数量
  - `grep -c "@router\." apps/stock-assistant/backend/src/quantpilot_stock/api/execution.py` 输出 ≥ 4

- [ ] **AC-3**: 测试通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run pytest tests/test_execution_api.py -v)` 退出码 0
  - 至少 8 个测试

- [ ] **AC-4**: mypy 通过
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run --isolated --with mypy python -m mypy src/quantpilot_stock/api/execution.py)` 退出码 0

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/api/execution.py`
- `apps/stock-assistant/backend/tests/test_execution_api.py`

修改：
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`
