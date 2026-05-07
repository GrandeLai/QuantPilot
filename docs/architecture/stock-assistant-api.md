# Stock-Assistant HTTP API Reference

**Backend**: `apps/stock-assistant/backend/` (Python, FastAPI)
**Port**: 8001 (dev)
**Base URL**: `http://localhost:8001/api`
**Last reviewed**: 2026-05-07

> **来源**：路由声明扫描自 `apps/stock-assistant/backend/src/quantpilot_stock/api/*.py`。运行 `(cd apps/stock-assistant/backend && uv run uvicorn quantpilot_stock.main:app --port 8001)` 后访问 `http://localhost:8001/docs` 可看自动生成的 OpenAPI 交互文档（Swagger UI）。
>
> 这份文档不重复 Swagger 内容；它列出**全部路由清单 + 业务语义分组**，供检索和理解 API 全貌。

---

## 路由模块总览

| 模块 | Prefix | 业务域 | 路由数 |
|---|---|---|---|
| `alerts.py` | `/api/alerts` | 告警系统（规则、事件、检查） | 5 |
| `advisor.py` | `/api/advisor` | 股票 / 加密机会与风险卡片 | 5 |
| `crypto.py` | `/api/crypto` | OKX 加密：现货、永续合约、期权 | 18 |
| `data.py` | `/api/data` | 行情拉取与查询 | 9 |
| `insights.py` | `/api/insights` | 市场体制 / 相关性洞察 | 2 |
| `options.py` | `/api/options` | 期权希腊字母 / IV / 情景 | 4 |
| `paper.py` | `/api/paper` | 模拟盘 session 与订单 | 8 |
| `platform.py` | `/api/platform` | 平台状态汇总 | 1 |
| `portfolio.py` | `/api/portfolio` | 组合策略与权益 | 7 |
| `screener.py` | `/api/screener` | 选股 / 选币 + 评分 + 同行 / 宏观 | 8 |
| `security.py` | `/api/security` | API Key 管理（keyring） | 4 |
| `sentiment.py` | `/api/sentiment` | 新闻情绪 | 2 |
| `trading.py` | `/api/trading` | 多 broker 统一交易接口 | 17 |
| `ws.py` | `/ws` | WebSocket（行情 + 信号） | 2 |

健康检查 `GET /healthz` 由 `main.py` 直接暴露。

---

## 详细端点清单

### GET /healthz

存活检查；返回 `{"status": "ok", ...}`。直接定义在 `main.py`，不带 `/api` 前缀。

---

### `alerts.py` — 告警系统（5）

| 方法 | 路径 |
|---|---|
| GET | `/api/alerts/rules` |
| POST | `/api/alerts/rules` |
| DELETE | `/api/alerts/rules/{rule_id}` |
| GET | `/api/alerts/events` |
| POST | `/api/alerts/check` |

支持的规则类型：价格阈值、指标交叉、新闻情绪、自定义事件。触发后通过 `quantpilot_stock.alerts.notifiers` 发送（飞书 / Telegram）。

---

### `advisor.py` — 投资助手（5）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/advisor/overview` | 组合总览 |
| GET | `/api/advisor/opportunities` | 美股机会卡片，支持 `symbols=AAPL,NVDA` |
| GET | `/api/advisor/risks` | 美股风险卡片，支持 `symbols=AAPL,NVDA` |
| GET | `/api/advisor/crypto/opportunities` | 加密机会卡片 |
| GET | `/api/advisor/crypto/risks` | 加密风险卡片 |

---

### `crypto.py` — OKX 加密交易（18）

#### 现货（10）
| 方法 | 路径 |
|---|---|
| GET | `/api/crypto/status` |
| GET | `/api/crypto/pairs` |
| GET | `/api/crypto/ticker` |
| GET | `/api/crypto/price/{symbol}` |
| GET | `/api/crypto/account` |
| GET | `/api/crypto/orders/open` |
| GET | `/api/crypto/orders/history` |
| POST | `/api/crypto/orders` |
| DELETE | `/api/crypto/orders/{order_id}` |
| GET | `/api/crypto/futures/tickers` |

#### 永续合约（4）
| 方法 | 路径 |
|---|---|
| GET | `/api/crypto/futures/positions` |
| GET | `/api/crypto/futures/orders/open` |
| POST | `/api/crypto/futures/orders` |
| DELETE | `/api/crypto/futures/orders/{order_id}` |

#### 期权（4）
| 方法 | 路径 |
|---|---|
| GET | `/api/crypto/options/underlyings` |
| GET | `/api/crypto/options/expiries` |
| GET | `/api/crypto/options/chain` |
| GET | `/api/crypto/options/positions` |

---

### `data.py` — 行情数据（9）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/data/bars` | 拉历史 K 线（OHLCV） |
| POST | `/api/data/fetch` | 触发后台拉取 + 入库 |
| GET | `/api/data/symbols` | 已入库标的列表 |
| GET | `/api/data/universe` | 双产品共享支持市场宇宙，可用 `product=quant-assistant|stock-assistant` 过滤 |
| GET | `/api/data/range` | 已存数据时间区间 |
| GET | `/api/data/onchain/btc` | BTC 链上指标列表 |
| GET | `/api/data/prices` | 批量最新价 |
| GET | `/api/data/prices/{symbol}` | 单标的最新价 |
| GET | `/api/data/onchain/btc/{metric}` | 单个 BTC 链上指标历史 |

数据源：yfinance（美 / 港股）、akshare（A 股）、OKX（加密）、glassnode/coinmetrics（链上）。写入端：`quantpilot_common.data.storage` → `common/data-store/market.duckdb`。

---

### `insights.py` — 市场洞察（2）

| 方法 | 路径 |
|---|---|
| POST | `/api/insights/regime` |
| POST | `/api/insights/correlate` |

---

### `options.py` — 期权分析（4）

| 方法 | 路径 |
|---|---|
| POST | `/api/options/greeks` |
| POST | `/api/options/implied-vol` |
| POST | `/api/options/sensitivity` |
| POST | `/api/options/scenario` |

---

### `paper.py` — 模拟盘（8）

| 方法 | 路径 |
|---|---|
| POST | `/api/paper/sessions` |
| GET | `/api/paper/sessions` |
| GET | `/api/paper/sessions/{session_id}` |
| DELETE | `/api/paper/sessions/{session_id}` |
| POST | `/api/paper/sessions/{session_id}/orders` |
| GET | `/api/paper/sessions/{session_id}/orders` |
| POST | `/api/paper/sessions/{session_id}/orders/enqueue` |
| GET | `/api/paper/sessions/{session_id}/orders/queue` |

队列实现：Redis Streams（`orders:{session_id}`），见 `quantpilot_common/redis/order_queue.py`。

---

### `platform.py` — 平台总览（1）

| 方法 | 路径 |
|---|---|
| GET | `/api/platform/summary` |

返回各 provider 状态 + Redis / DB 连通性 + 配置摘要。

---

### `portfolio.py` — 组合管理（7）

| 方法 | 路径 |
|---|---|
| POST | `/api/portfolio/strategies` |
| GET | `/api/portfolio/strategies` |
| DELETE | `/api/portfolio/strategies/{name}` |
| GET | `/api/portfolio/summary` |
| GET | `/api/portfolio/equity` |
| GET | `/api/portfolio/correlation` |
| GET | `/api/portfolio/available-strategies` |

---

### `screener.py` — 选股 / 选币（8）

| 方法 | 路径 |
|---|---|
| GET | `/api/screener/strategies` |
| POST | `/api/screener/screen` |
| GET | `/api/screener/score/{symbol}` |
| POST | `/api/screener/analyze/{symbol}` |
| GET | `/api/screener/market` |
| GET | `/api/screener/fundamentals/{symbol}` |
| GET | `/api/screener/macro` |
| GET | `/api/screener/peers/{symbol}` |

---

### `security.py` — API Key 管理（4）

| 方法 | 路径 |
|---|---|
| GET | `/api/security/providers` |
| POST | `/api/security/keys/{provider}` |
| GET | `/api/security/keys/{provider}` |
| DELETE | `/api/security/keys/{provider}` |

OS keyring 加密；密文不出本机。

---

### `sentiment.py` — 新闻情绪（2）

| 方法 | 路径 |
|---|---|
| GET | `/api/sentiment/news` |
| GET | `/api/sentiment/history` |

VADER + RSS 拉新闻 → 打分。

---

### `trading.py` — 统一交易（17）

#### 状态 / 查询（10）
| 方法 | 路径 |
|---|---|
| GET | `/api/trading/status` |
| GET | `/api/trading/risk` |
| GET | `/api/trading/securities/search` |
| GET | `/api/trading/quotes` |
| GET | `/api/trading/account` |
| GET | `/api/trading/positions` |
| GET | `/api/trading/orders/today` |
| GET | `/api/trading/orders/history` |
| GET | `/api/trading/orders/{order_id}` |
| GET | `/api/trading/orders/{order_id}/events` |

#### 订单管理（4）
| 方法 | 路径 |
|---|---|
| GET | `/api/trading/orders/{order_id}/report` |
| POST | `/api/trading/orders/estimate` |
| POST | `/api/trading/orders` |
| DELETE | `/api/trading/orders/{order_id}` |

#### 成交 / 资金流（3）
| 方法 | 路径 |
|---|---|
| GET | `/api/trading/executions/today` |
| GET | `/api/trading/executions/history` |
| GET | `/api/trading/cash-flows` |

支持 broker：Longbridge（主）、FuTu、Mock，统一返回 `TradingProvider*` 数据形状。

---

### `ws.py` — WebSocket（2）

| 协议 | 路径 |
|---|---|
| WS | `/ws/bars/{symbol}/{timeframe}` |
| WS | `/ws/signals` |

实时 K 线 / 信号广播；前端用 `LiveDataPanel.tsx` 订阅。

---

## 调试

```bash
# 启动
./scripts/dev-stock.sh

# Swagger UI
open http://localhost:8001/docs

# OpenAPI JSON
curl http://localhost:8001/openapi.json | jq

# 健康检查
curl http://localhost:8001/healthz
```

---

## 与 quant-assistant 的对照

`quant-assistant`（端口 8002）只暴露 6 个 HTTP 端点，全部为无状态计算（详见 [`quant-assistant-api.md`](quant-assistant-api.md)）。两 app 的边界：

| 维度 | stock-assistant | quant-assistant |
|---|---|---|
| 端点数 | ~92（含 WS） | 6 |
| 状态 | 重（broker 会话、paper sessions、Redis 缓存） | 无（每次请求独立计算） |
| 数据 | 写 market.duckdb | 不读不写共享 db；从请求 body 拿数据 |
| 业务领域 | 人决策交易 | 自动化量化研究 |
