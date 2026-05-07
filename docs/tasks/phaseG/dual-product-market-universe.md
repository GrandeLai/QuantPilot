# Task phaseG.dual-product-market-universe: 双产品共享市场宇宙

**Phase**: G
**Status**: completed
**Created**: 2026-05-07

---

## 范围

### 做什么

- 明确 `quant-assistant`（量化投资）与 `stock-assistant`（股票投资助手）都支持美股、ETF、港股、A 股与 OKX 加密标的。
- 在 `common/python/quantpilot_common/data/universe.py` 定义共享市场宇宙。
- 在 `common/frontend-components/src/markets.ts` 导出同一套前端可用市场宇宙。
- 在 stock-assistant 暴露 `GET /data/universe` / `GET /api/data/universe`。
- 让 quant 前端回测页可选择共享市场宇宙中的标的，并在缺少 K 线时通过 stock-assistant 数据层拉取。

### 不做什么

- 不引入新数据源依赖。
- 不改变 DuckDB 单写协议：仍然只有 stock-assistant 写 `market.duckdb`。
- 不让投资助手直接下单。

---

## 验收标准

- [x] **AC-1**: 共享 Python market universe 同时包含美股与加密标的，并对两个产品可见。
- [x] **AC-2**: stock-assistant 提供 `/data/universe` API，支持按 `product` 过滤。
- [x] **AC-3**: quant-assistant 前端回测入口展示共享市场标的，并能按标的默认数据源触发补数。
- [x] **AC-4**: stock-assistant assistant 前端展示同一套支持市场范围。
- [x] **AC-5**: 文档说明双产品边界、资产支持范围与 DuckDB 写权限不变。

---

## 测试集合

```bash
(cd common/python && uv run pytest tests/test_market_universe.py -q)
(cd apps/stock-assistant/backend && uv run pytest tests/test_data_api.py -q)
(cd common/frontend-components && npm run build)
(cd apps/quant-assistant/frontend && npm run build)
(cd apps/stock-assistant/frontends/assistant && npm run build)
```
