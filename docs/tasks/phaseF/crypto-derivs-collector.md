# Task phaseF.crypto-derivs-collector: Binance + OKX 衍生品数据采集

**Phase**: Phase F.1（加密衍生品面板之 1）
**Status**: pending
**Implementation PR**: <pending>
**Created**: 2026-04-29
**Owner-agent**: implementation-agent
**Reviewer-agent**: acceptance-agent

---

## 范围

### 背景

Brainstorm Top-5 #2 (加密资金面板) 第 1 个子任务。本任务实现纯 collector 层：从 Binance 永续合约 / OKX SWAP 公开 API 拉取 funding rate + open interest，零 API key 即可工作。后续 F.1.11 (basis 计算) / F.1.13 (前端) 都消费这层。

### 数据源（全部公共 API，无需 API key）

- **Binance Futures**:
  - Current funding: `GET https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT`
  - Open interest: `GET https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT`
  - Historical funding: `GET https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=100`
- **OKX**:
  - Current funding: `GET https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP`
  - Open interest: `GET https://www.okx.com/api/v5/public/open-interest?instType=SWAP&instId=BTC-USDT-SWAP`
  - Historical funding: `GET https://www.okx.com/api/v5/public/funding-rate-history?instId=BTC-USDT-SWAP&limit=100`

### 做什么

新增子包 `quantpilot_stock.crypto_derivs/`：

#### 1. `models.py`

Pydantic v2 类型（用于 API 边界 + 类型对齐）：

```python
class FundingRate(BaseModel):
    exchange: Literal["binance", "okx"]
    symbol: str           # 标准化为 "BTC", "ETH" 等 base asset
    raw_symbol: str       # 交易所原始格式，如 "BTCUSDT" 或 "BTC-USDT-SWAP"
    funding_rate: float   # 8h funding 比率（如 0.0001 = 0.01%）
    next_funding_time: datetime | None
    timestamp: datetime

class OpenInterest(BaseModel):
    exchange: Literal["binance", "okx"]
    symbol: str
    raw_symbol: str
    open_interest: float       # 张数或合约数（交易所原生单位）
    open_interest_value: float | None  # 美元价值（OKX 直接给，Binance 算）
    timestamp: datetime
```

#### 2. `collector.py` — 异步 fetcher

```python
async def fetch_binance_funding(asset: str, *, client: httpx.AsyncClient | None = None) -> FundingRate
async def fetch_binance_open_interest(asset: str, *, client: httpx.AsyncClient | None = None) -> OpenInterest
async def fetch_binance_funding_history(asset: str, limit: int = 100, *, client: httpx.AsyncClient | None = None) -> list[FundingRate]

async def fetch_okx_funding(asset: str, *, client: httpx.AsyncClient | None = None) -> FundingRate
async def fetch_okx_open_interest(asset: str, *, client: httpx.AsyncClient | None = None) -> OpenInterest
async def fetch_okx_funding_history(asset: str, limit: int = 100, *, client: httpx.AsyncClient | None = None) -> list[FundingRate]

async def fetch_aggregated_derivs(asset: str = "BTC") -> dict
    # 并发拉取 binance + okx 当前 funding + OI，返回:
    # {
    #   "asset": "BTC",
    #   "timestamp": ISO,
    #   "funding": {"binance": FundingRate, "okx": FundingRate},
    #   "open_interest": {"binance": OI, "okx": OI},
    #   "errors": {"binance_funding": "...", ...}  # 失败的项
    # }
```

约定：
- `asset` 大写 base asset（"BTC"/"ETH"/"SOL"）；内部映射成 `BTCUSDT` / `BTC-USDT-SWAP`
- `client` 参数允许复用同一个 AsyncClient（连接池），不传则内部 new+close
- HTTP 4xx/5xx → raise `httpx.HTTPStatusError`（不吃错误）
- `fetch_aggregated_derivs` 用 `asyncio.gather(..., return_exceptions=True)`，单个失败收集到 `errors` dict 中而不抛

#### 3. `__init__.py`

re-export 公共 fetcher + 模型。

#### 4. 测试 `tests/test_crypto_derivs_collector.py`

用 `respx`（已不可用）或 `httpx.MockTransport` 模拟响应。**因为不能新增依赖**，使用 `httpx.MockTransport` 内置能力。

至少 12 个测试用例：每个 fetcher happy path + Binance 错误响应 + OKX 错误响应 + asset 标准化（小写 → 大写）+ aggregated 部分失败场景。

### 不做什么

- 不做 Bybit / Deribit（推迟到完整版）
- 不做 ETF flow（F.1.12 单独任务）
- 不做 basis 计算（F.1.11 单独任务）
- 不做 API 路由（最后一个任务统一接）
- 不引入新依赖（httpx 已有）
- 不做 WebSocket 实时（REST 即可）

---

## 验收标准

- [ ] **AC-1**: 文件存在
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/crypto_derivs/__init__.py`
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/crypto_derivs/models.py`
  - `test -f apps/stock-assistant/backend/src/quantpilot_stock/crypto_derivs/collector.py`
  - `test -f apps/stock-assistant/backend/tests/test_crypto_derivs_collector.py`
- [ ] **AC-2**: import 烟雾测试 — `(cd apps/stock-assistant/backend && uv run python -c "from quantpilot_stock.crypto_derivs import fetch_binance_funding, fetch_binance_open_interest, fetch_okx_funding, fetch_okx_open_interest, fetch_aggregated_derivs, FundingRate, OpenInterest")` 退出码 0
- [ ] **AC-3**: 单测全过 — `(cd apps/stock-assistant/backend && uv run pytest tests/test_crypto_derivs_collector.py -v)` 退出码 0；用例数 ≥ 12
- [ ] **AC-4**: ruff 干净 — `(cd apps/stock-assistant/backend && uv run --with ruff ruff check src/quantpilot_stock/crypto_derivs/ tests/test_crypto_derivs_collector.py)`
- [ ] **AC-5**: mypy 干净 — `(cd apps/stock-assistant/backend && uv run --with mypy mypy src/quantpilot_stock/crypto_derivs/ --ignore-missing-imports)`
- [ ] **AC-6**: 不引入新依赖 — `git diff main -- apps/stock-assistant/backend/pyproject.toml` 输出为空
- [ ] **AC-7**: 现有测试无回归 — `(cd apps/stock-assistant/backend && uv run pytest tests/ -x --ignore=tests/test_crypto_derivs_collector.py -q)` 退出码 0
- [ ] **AC-8**: 不动其它 app — `git diff main --name-only -- apps/quant-assistant/ common/ tools/` 输出为空（除非属于 docs/）
- [ ] **AC-9**: 测试不真正发起网络请求 — `grep -c "MockTransport\|mock_transport" apps/stock-assistant/backend/tests/test_crypto_derivs_collector.py` ≥ 1（确保使用 mock）

---

## 测试集合

```bash
(cd apps/stock-assistant/backend && uv run pytest tests/test_crypto_derivs_collector.py -v)
(cd apps/stock-assistant/backend && uv run --with ruff ruff check src/quantpilot_stock/crypto_derivs/ tests/test_crypto_derivs_collector.py)
(cd apps/stock-assistant/backend && uv run --with mypy mypy src/quantpilot_stock/crypto_derivs/ --ignore-missing-imports)
(cd apps/stock-assistant/backend && uv run python -c "from quantpilot_stock.crypto_derivs import fetch_binance_funding, fetch_binance_open_interest, fetch_okx_funding, fetch_okx_open_interest, fetch_aggregated_derivs, FundingRate, OpenInterest; print('ok')")
(cd apps/stock-assistant/backend && uv run pytest tests/ -x --ignore=tests/test_crypto_derivs_collector.py -q)
git diff main -- apps/stock-assistant/backend/pyproject.toml
```

---

## 文件影响范围

新建：
- `apps/stock-assistant/backend/src/quantpilot_stock/crypto_derivs/__init__.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/crypto_derivs/models.py`
- `apps/stock-assistant/backend/src/quantpilot_stock/crypto_derivs/collector.py`
- `apps/stock-assistant/backend/tests/test_crypto_derivs_collector.py`
- `docs/tasks/phaseF/crypto-derivs-collector.md`

不允许改：所有其它路径。

---

## 引用

- **设计来源**：plan §2 Top-5 #2；F.1 README
- **上游依赖**：无（纯外部 API，零依赖任务）
- **下游依赖**：F.1.11 (basis), F.1.13 (前端) 都消费此 collector
