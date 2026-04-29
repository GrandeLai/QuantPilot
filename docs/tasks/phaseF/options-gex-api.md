# Task phaseF.options-gex-api: GEX FastAPI 端点

**Phase**: Phase F.1  
**Status**: pending  
**Created**: 2026-04-29

---

## 范围

新建 `apps/stock-assistant/backend/src/quantpilot_stock/api/gex.py`，注册进 `main.py`。

### Endpoints

```
GET /options/gex/snapshot?ticker=SPY&max_dte=45&min_oi=10&r=0.05
GET /options/gex/levels?ticker=SPY&max_dte=45
```

- `snapshot`: 返回完整 `GEXSnapshot`（含 `gex_by_strike` 列表）
- `levels`: 仅返回 `{ gamma_flip_level, major_magnet, high_vol_trigger, net_gex_total, spot }`
- 若 fetch 失败（网络/无数据）→ 503 with `{"detail": "options chain unavailable"}`

---

## 验收标准

- [ ] **AC-1**: 文件 + 路由存在
  - `grep -q "gex_router\|gex" apps/stock-assistant/backend/src/quantpilot_stock/main.py`
- [ ] **AC-2**: snapshot 端点存在
  - `grep -q "/snapshot\|/levels" apps/stock-assistant/backend/src/quantpilot_stock/api/gex.py`
- [ ] **AC-3**: 测试通过（mock fetch_chain_yfinance）
  - `(cd apps/stock-assistant/backend && export GVM_ROOT=/Users/bytedance/.gvm && uv run --group dev pytest tests/test_options_gex_api.py -v)` 退出码 0
- [ ] **AC-4**: mypy clean

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/api/gex.py`
- `apps/stock-assistant/backend/tests/test_options_gex_api.py`

修改：
- `apps/stock-assistant/backend/src/quantpilot_stock/main.py`
