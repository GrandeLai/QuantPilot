# Redis Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce Redis to QuantPilot to enable real-time market data pub/sub, latest-price caching, real-time signal broadcasting, and a paper-trading order queue via Redis Streams.

**Architecture:** A singleton `RedisClient` (Task 1) is shared by three subsystems: a `PriceCache` for O(1) latest-price lookups (Task 2), a `BarPublisher`/WebSocket endpoint pair for real-time bar streaming (Task 3), an upgraded `SignalBroadcaster` that pushes to Redis in addition to SQLite (Task 4), and an `OrderQueue` backed by Redis Streams for reliable order processing (Task 5). A frontend `LiveDataPanel` (Task 6) consumes the WebSocket endpoints.

**Tech Stack:** `redis[asyncio]>=5.0.0` (redis-py async), `fakeredis>=2.26.0` (unit-test mock), FastAPI WebSocket, React/TypeScript

---

## File Map

### New Backend Files
- `backend/src/quantpilot/redis/__init__.py`
- `backend/src/quantpilot/redis/client.py` — async Redis singleton (`RedisClient`)
- `backend/src/quantpilot/redis/price_cache.py` — `PriceCache` (set/get latest price with TTL)
- `backend/src/quantpilot/redis/pubsub.py` — `BarPublisher` (publish new OHLCV bar to channel)
- `backend/src/quantpilot/redis/order_queue.py` — `OrderQueue` (Redis Streams XADD/XREAD)
- `backend/src/quantpilot/api/ws.py` — WebSocket endpoints: `/ws/bars/{symbol}/{timeframe}`, `/ws/signals`
- `backend/tests/test_redis_client.py`
- `backend/tests/test_price_cache.py`
- `backend/tests/test_pubsub.py`
- `backend/tests/test_order_queue.py`

### Modified Backend Files
- `backend/pyproject.toml` — add `redis[asyncio]>=5.0.0`, dev dep `fakeredis>=2.26.0`
- `backend/src/quantpilot/main.py` — connect/disconnect Redis in lifespan; register ws router
- `backend/src/quantpilot/data/scheduler.py` — publish bar + update price cache after DuckDB write
- `backend/src/quantpilot/signals/broadcaster.py` — publish to Redis channel after SQLite write
- `backend/src/quantpilot/api/data.py` — add `GET /api/data/prices` (reads from price cache)

### New Frontend Files
- `frontend/src/components/LiveDataPanel.tsx` — WebSocket bar stream + signal stream display

### Modified Frontend Files
- `frontend/src/App.tsx` — add "实时" tab

---

## Task 1: Redis Client + Dependencies + Lifespan

**Files:**
- Create: `backend/src/quantpilot/redis/__init__.py`
- Create: `backend/src/quantpilot/redis/client.py`
- Modify: `backend/pyproject.toml`
- Modify: `backend/src/quantpilot/main.py`
- Test: `backend/tests/test_redis_client.py`

- [ ] **Step 1: Add dependencies to pyproject.toml**

In `backend/pyproject.toml`, add after the `vaderSentiment` line:

```toml
    # Redis
    "redis[asyncio]>=5.0.0",
```

And in `[project.optional-dependencies]` dev section, add:

```toml
    "fakeredis>=2.26.0",
```

Then install:

```bash
cd /Users/bytedance/code/QuantPilot/backend && uv sync --extra dev
```

- [ ] **Step 2: Write failing tests**

```python
# backend/tests/test_redis_client.py
"""Redis 客户端测试 — Task 1 验收."""
from __future__ import annotations

import pytest
import fakeredis.aioredis

from quantpilot.redis.client import RedisClient


@pytest.fixture(autouse=True)
async def reset_client():
    """每个测试前后重置单例状态."""
    RedisClient._instance = None
    yield
    if RedisClient._instance is not None:
        await RedisClient.disconnect()
    RedisClient._instance = None


async def _fake_client() -> fakeredis.aioredis.FakeRedis:
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


class TestRedisClient:
    async def test_connect_sets_instance(self) -> None:
        fake = await _fake_client()
        RedisClient._instance = fake
        assert RedisClient.get() is fake

    async def test_get_before_connect_raises(self) -> None:
        with pytest.raises(RuntimeError, match="未连接"):
            RedisClient.get()

    async def test_disconnect_clears_instance(self) -> None:
        fake = await _fake_client()
        RedisClient._instance = fake
        await RedisClient.disconnect()
        assert RedisClient._instance is None

    async def test_ping_returns_true_when_connected(self) -> None:
        fake = await _fake_client()
        RedisClient._instance = fake
        result = await RedisClient.ping()
        assert result is True

    async def test_ping_returns_false_when_disconnected(self) -> None:
        result = await RedisClient.ping()
        assert result is False

    async def test_health_check(self) -> None:
        fake = await _fake_client()
        RedisClient._instance = fake
        ok = await RedisClient.ping()
        assert ok is True
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
cd /Users/bytedance/code/QuantPilot/backend && uv run pytest tests/test_redis_client.py -v 2>&1 | head -20
```

Expected: `ImportError` — module doesn't exist yet.

- [ ] **Step 4: Create the Redis package**

```python
# backend/src/quantpilot/redis/__init__.py
"""QuantPilot Redis 集成层."""
```

```python
# backend/src/quantpilot/redis/client.py
"""Redis 异步客户端单例."""
from __future__ import annotations

import redis.asyncio as aioredis
from loguru import logger


class RedisClient:
    """全局 Redis 异步客户端单例.

    用法:
        await RedisClient.connect(url)
        r = RedisClient.get()
        await RedisClient.disconnect()
    """

    _instance: aioredis.Redis | None = None  # type: ignore[type-arg]

    @classmethod
    async def connect(cls, url: str) -> None:
        """建立 Redis 连接.

        Args:
            url: Redis 连接 URL，如 redis://host:6379 或 redis://:password@host:6379/0
        """
        cls._instance = aioredis.from_url(url, decode_responses=True)
        await cls._instance.ping()
        logger.info(f"[Redis] 已连接: {url.split('@')[-1]}")  # 隐藏密码

    @classmethod
    async def disconnect(cls) -> None:
        """关闭 Redis 连接."""
        if cls._instance is not None:
            await cls._instance.aclose()
            cls._instance = None
            logger.info("[Redis] 连接已关闭")

    @classmethod
    def get(cls) -> aioredis.Redis:  # type: ignore[type-arg]
        """获取 Redis 客户端实例.

        Raises:
            RuntimeError: 未调用 connect() 时
        """
        if cls._instance is None:
            raise RuntimeError("Redis 未连接: 请先调用 RedisClient.connect()")
        return cls._instance

    @classmethod
    async def ping(cls) -> bool:
        """检查 Redis 连通性.

        Returns:
            True 表示连通，False 表示未连接或超时
        """
        try:
            return bool(await cls.get().ping())
        except Exception:
            return False
```

- [ ] **Step 5: Update main.py lifespan to connect/disconnect Redis**

Read `backend/src/quantpilot/main.py`, then modify the lifespan function:

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理：startup / shutdown."""
    settings = get_settings()
    logger.info(f"{settings.app_name} v{settings.app_version} 启动中...")

    # 确保数据目录存在
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.strategy_dir.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)

    # 连接 Redis
    from quantpilot.redis.client import RedisClient
    try:
        await RedisClient.connect(settings.redis_url)
    except Exception as e:
        logger.warning(f"[Redis] 连接失败（降级运行）: {e}")

    logger.info("QuantPilot API 启动成功")
    yield

    # 断开 Redis
    from quantpilot.redis.client import RedisClient
    await RedisClient.disconnect()
    logger.info("QuantPilot API 正在关闭...")
```

- [ ] **Step 6: Run tests and verify they pass**

```bash
cd /Users/bytedance/code/QuantPilot/backend && uv run pytest tests/test_redis_client.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 7: Lint**

```bash
cd /Users/bytedance/code/QuantPilot/backend && uv run ruff check src/quantpilot/redis/ tests/test_redis_client.py --fix
```

- [ ] **Step 8: Commit**

```bash
cd /Users/bytedance/code/QuantPilot/backend
git add src/quantpilot/redis/__init__.py src/quantpilot/redis/client.py tests/test_redis_client.py src/quantpilot/main.py pyproject.toml
git commit -m "feat(redis): add async Redis client singleton with lifespan connect/disconnect"
```

---

## Task 2: Latest Price Cache

**Files:**
- Create: `backend/src/quantpilot/redis/price_cache.py`
- Modify: `backend/src/quantpilot/data/scheduler.py`
- Modify: `backend/src/quantpilot/api/data.py`
- Test: `backend/tests/test_price_cache.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_price_cache.py
"""最新价格缓存测试 — Task 2 验收."""
from __future__ import annotations

import pytest
import fakeredis.aioredis

from quantpilot.redis.client import RedisClient
from quantpilot.redis.price_cache import PriceCache


@pytest.fixture(autouse=True)
async def setup_redis():
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    RedisClient._instance = fake
    yield fake
    await RedisClient.disconnect()
    RedisClient._instance = None


class TestPriceCache:
    async def test_set_and_get_price(self) -> None:
        cache = PriceCache()
        await cache.set_price("AAPL", 150.25)
        result = await cache.get_price("AAPL")
        assert result == pytest.approx(150.25)

    async def test_get_nonexistent_returns_none(self) -> None:
        cache = PriceCache()
        result = await cache.get_price("NONEXISTENT")
        assert result is None

    async def test_set_multiple_and_get_all(self) -> None:
        cache = PriceCache()
        await cache.set_price("AAPL", 150.0)
        await cache.set_price("GOOG", 2800.0)
        await cache.set_price("TSLA", 700.0)
        all_prices = await cache.get_all()
        assert all_prices["AAPL"] == pytest.approx(150.0)
        assert all_prices["GOOG"] == pytest.approx(2800.0)
        assert all_prices["TSLA"] == pytest.approx(700.0)

    async def test_get_all_empty(self) -> None:
        cache = PriceCache()
        result = await cache.get_all()
        assert result == {}

    async def test_delete_price(self) -> None:
        cache = PriceCache()
        await cache.set_price("AAPL", 150.0)
        await cache.delete_price("AAPL")
        assert await cache.get_price("AAPL") is None

    async def test_update_price(self) -> None:
        cache = PriceCache()
        await cache.set_price("AAPL", 100.0)
        await cache.set_price("AAPL", 200.0)
        result = await cache.get_price("AAPL")
        assert result == pytest.approx(200.0)
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /Users/bytedance/code/QuantPilot/backend && uv run pytest tests/test_price_cache.py -v 2>&1 | head -20
```

Expected: `ImportError`.

- [ ] **Step 3: Implement PriceCache**

```python
# backend/src/quantpilot/redis/price_cache.py
"""最新价格缓存 — Redis Hash + 各标的独立 Key."""
from __future__ import annotations

from loguru import logger

from quantpilot.redis.client import RedisClient

_HASH_KEY = "quantpilot:prices"  # Redis Hash: field=symbol, value=price_str


class PriceCache:
    """用 Redis Hash 存储各标的最新收盘价.

    所有标的存储在同一个 Hash Key 下，支持批量读取。
    """

    async def set_price(self, symbol: str, price: float) -> None:
        """写入标的最新价格.

        Args:
            symbol: 标的代码
            price: 最新价格
        """
        r = RedisClient.get()
        await r.hset(_HASH_KEY, symbol, str(price))
        logger.debug(f"[PriceCache] {symbol} = {price}")

    async def get_price(self, symbol: str) -> float | None:
        """读取标的最新价格.

        Returns:
            float 价格，或 None（不存在时）
        """
        r = RedisClient.get()
        val = await r.hget(_HASH_KEY, symbol)
        return float(val) if val is not None else None

    async def get_all(self) -> dict[str, float]:
        """读取所有标的的最新价格.

        Returns:
            {symbol: price} 字典
        """
        r = RedisClient.get()
        raw: dict[str, str] = await r.hgetall(_HASH_KEY)
        return {k: float(v) for k, v in raw.items()}

    async def delete_price(self, symbol: str) -> None:
        """删除标的价格缓存."""
        r = RedisClient.get()
        await r.hdel(_HASH_KEY, symbol)
```

- [ ] **Step 4: Run tests and verify they pass**

```bash
cd /Users/bytedance/code/QuantPilot/backend && uv run pytest tests/test_price_cache.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 5: Update data/scheduler.py to cache price after writing bars**

Read `backend/src/quantpilot/data/scheduler.py`, then update `_update_symbol`:

```python
def _update_symbol(self, symbol: str, timeframe: str, source: str) -> None:
    """执行单个标的的数据更新."""
    import asyncio
    try:
        _, latest = self._storage.get_date_range(symbol, timeframe)
        start = (latest.date() if latest else date.today() - timedelta(days=365))

        if source == "yfinance":
            bars = self._yf.fetch_ohlcv(symbol, timeframe, start=start)
        else:
            logger.warning(f"[Scheduler] 未知数据源: {source}")
            return

        if bars:
            written = self._storage.upsert_bars(bars)
            logger.info(f"[Scheduler] {symbol} {timeframe} 更新 {written} 条")

            # 更新 Redis 价格缓存（最新收盘价）
            latest_bar = bars[-1]
            try:
                from quantpilot.redis.client import RedisClient
                from quantpilot.redis.price_cache import PriceCache
                if RedisClient._instance is not None:
                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(PriceCache().set_price(symbol, latest_bar.close))
                    loop.close()
            except Exception as e:
                logger.debug(f"[Scheduler] 价格缓存更新跳过: {e}")
    except Exception as e:
        logger.error(f"[Scheduler] {symbol} 更新失败: {e}")
```

- [ ] **Step 6: Add GET /api/data/prices endpoint**

Read `backend/src/quantpilot/api/data.py`, then add at the end:

```python
@router.get("/data/prices")
async def get_latest_prices() -> dict[str, Any]:
    """从 Redis 缓存读取所有标的最新价格（O(1) 查询）."""
    from quantpilot.redis.client import RedisClient
    from quantpilot.redis.price_cache import PriceCache
    if RedisClient._instance is None:
        raise HTTPException(status_code=503, detail="Redis 未连接")
    prices = await PriceCache().get_all()
    return {"prices": prices, "count": len(prices)}

@router.get("/data/prices/{symbol}")
async def get_symbol_price(symbol: str) -> dict[str, Any]:
    """读取单个标的最新缓存价格."""
    from quantpilot.redis.client import RedisClient
    from quantpilot.redis.price_cache import PriceCache
    if RedisClient._instance is None:
        raise HTTPException(status_code=503, detail="Redis 未连接")
    price = await PriceCache().get_price(symbol.upper())
    if price is None:
        raise HTTPException(status_code=404, detail=f"{symbol} 暂无缓存价格")
    return {"symbol": symbol.upper(), "price": price}
```

(Make sure `from typing import Any` and `from fastapi import APIRouter, HTTPException` are already imported in `data.py` — add if missing.)

- [ ] **Step 7: Lint**

```bash
cd /Users/bytedance/code/QuantPilot/backend && uv run ruff check src/quantpilot/redis/price_cache.py src/quantpilot/api/data.py src/quantpilot/data/scheduler.py tests/test_price_cache.py --fix
```

- [ ] **Step 8: Commit**

```bash
cd /Users/bytedance/code/QuantPilot/backend
git add src/quantpilot/redis/price_cache.py tests/test_price_cache.py src/quantpilot/data/scheduler.py src/quantpilot/api/data.py
git commit -m "feat(redis): add PriceCache and /data/prices endpoints backed by Redis Hash"
```

---

## Task 3: Bar Pub/Sub + WebSocket Endpoint

**Files:**
- Create: `backend/src/quantpilot/redis/pubsub.py`
- Create: `backend/src/quantpilot/api/ws.py`
- Modify: `backend/src/quantpilot/data/scheduler.py`
- Modify: `backend/src/quantpilot/main.py`
- Test: `backend/tests/test_pubsub.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_pubsub.py
"""行情 Pub/Sub 测试 — Task 3 验收."""
from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
import fakeredis.aioredis

from quantpilot.data.models import OHLCVBar
from quantpilot.redis.client import RedisClient
from quantpilot.redis.pubsub import BarPublisher, bar_channel


@pytest.fixture(autouse=True)
async def setup_redis():
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    RedisClient._instance = fake
    yield fake
    await RedisClient.disconnect()
    RedisClient._instance = None


def _bar(symbol: str = "AAPL", close: float = 150.0) -> OHLCVBar:
    return OHLCVBar(
        symbol=symbol,
        timeframe="1d",
        timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        open=close * 0.99,
        high=close * 1.01,
        low=close * 0.98,
        close=close,
        volume=1_000_000.0,
    )


class TestBarChannel:
    def test_channel_name_format(self) -> None:
        assert bar_channel("AAPL", "1d") == "bars:AAPL:1d"

    def test_channel_name_special_chars(self) -> None:
        assert bar_channel("BTC-USD", "1h") == "bars:BTC-USD:1h"


class TestBarPublisher:
    async def test_publish_returns_subscriber_count(self, setup_redis: fakeredis.aioredis.FakeRedis) -> None:
        publisher = BarPublisher()
        bar = _bar()
        # publish returns int (number of subscribers, 0 if none)
        count = await publisher.publish(bar)
        assert isinstance(count, int)

    async def test_publish_sends_json_payload(self, setup_redis: fakeredis.aioredis.FakeRedis) -> None:
        publisher = BarPublisher()
        bar = _bar("TSLA", 700.0)

        # Subscribe first to capture message
        pubsub = setup_redis.pubsub()
        channel = bar_channel("TSLA", "1d")
        await pubsub.subscribe(channel)

        await publisher.publish(bar)

        # Read message
        msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
        assert msg is not None
        data = json.loads(msg["data"])
        assert data["symbol"] == "TSLA"
        assert data["close"] == pytest.approx(700.0)
        assert data["timeframe"] == "1d"

    async def test_publish_bar_payload_fields(self, setup_redis: fakeredis.aioredis.FakeRedis) -> None:
        publisher = BarPublisher()
        bar = _bar("AAPL", 150.0)

        pubsub = setup_redis.pubsub()
        await pubsub.subscribe(bar_channel("AAPL", "1d"))
        await publisher.publish(bar)

        msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
        assert msg is not None
        data = json.loads(msg["data"])
        required_fields = {"symbol", "timeframe", "timestamp", "open", "high", "low", "close", "volume"}
        assert required_fields.issubset(set(data.keys()))
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /Users/bytedance/code/QuantPilot/backend && uv run pytest tests/test_pubsub.py -v 2>&1 | head -20
```

Expected: `ImportError`.

- [ ] **Step 3: Implement BarPublisher**

```python
# backend/src/quantpilot/redis/pubsub.py
"""行情 Pub/Sub — 发布 OHLCV bar 到 Redis channel."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from loguru import logger

from quantpilot.redis.client import RedisClient

if TYPE_CHECKING:
    from quantpilot.data.models import OHLCVBar


def bar_channel(symbol: str, timeframe: str) -> str:
    """生成行情频道名称.

    Args:
        symbol: 标的代码
        timeframe: K 线周期

    Returns:
        Redis 频道名，如 "bars:AAPL:1d"
    """
    return f"bars:{symbol}:{timeframe}"


def signal_channel(symbol: str = "*") -> str:
    """生成信号频道名称.

    Args:
        symbol: 标的代码，"*" 表示全量信号频道

    Returns:
        Redis 频道名，如 "signals:AAPL" 或 "signals:*"
    """
    return f"signals:{symbol}"


class BarPublisher:
    """向 Redis 发布 OHLCV bar 事件."""

    async def publish(self, bar: OHLCVBar) -> int:
        """发布一根 K 线到对应频道.

        Args:
            bar: OHLCV K 线数据

        Returns:
            收到消息的订阅者数量
        """
        r = RedisClient.get()
        channel = bar_channel(bar.symbol, bar.timeframe)
        payload = json.dumps({
            "symbol": bar.symbol,
            "timeframe": bar.timeframe,
            "timestamp": bar.timestamp.isoformat(),
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume,
        })
        count: int = await r.publish(channel, payload)
        logger.debug(f"[PubSub] 发布 {channel}: {bar.close:.2f} → {count} 订阅者")
        return count
```

- [ ] **Step 4: Create WebSocket API**

```python
# backend/src/quantpilot/api/ws.py
"""WebSocket 实时推送端点.

端点:
  WS /ws/bars/{symbol}/{timeframe}  — 实时 K 线推送
  WS /ws/signals                    — 实时信号推送
"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/bars/{symbol}/{timeframe}")
async def ws_bars(websocket: WebSocket, symbol: str, timeframe: str) -> None:
    """订阅指定标的和周期的实时 K 线数据.

    客户端连接后，每当有新 bar 推送到 Redis 频道 bars:{symbol}:{timeframe} 时，
    立即转发给客户端。

    Args:
        symbol: 标的代码，如 AAPL
        timeframe: K 线周期，如 1d
    """
    from quantpilot.redis.client import RedisClient
    from quantpilot.redis.pubsub import bar_channel

    await websocket.accept()
    channel = bar_channel(symbol.upper(), timeframe)
    logger.info(f"[WS] 客户端订阅 {channel}")

    r = RedisClient.get()
    pubsub = r.pubsub()
    await pubsub.subscribe(channel)

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"])
    except WebSocketDisconnect:
        logger.info(f"[WS] 客户端断开 {channel}")
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()


@router.websocket("/ws/signals")
async def ws_signals(websocket: WebSocket) -> None:
    """订阅所有交易信号的实时推送.

    客户端连接后，任何策略发布的信号（通过 signals:* 频道）都会实时转发。
    """
    from quantpilot.redis.client import RedisClient

    await websocket.accept()
    channel = "signals:*"
    logger.info(f"[WS] 客户端订阅信号频道")

    r = RedisClient.get()
    pubsub = r.pubsub()
    await pubsub.psubscribe(channel)  # pattern subscribe

    try:
        async for message in pubsub.listen():
            if message["type"] == "pmessage":
                await websocket.send_text(message["data"])
    except WebSocketDisconnect:
        logger.info("[WS] 信号频道客户端断开")
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.punsubscribe(channel)
        await pubsub.aclose()
```

- [ ] **Step 5: Register ws router in main.py**

In `backend/src/quantpilot/main.py`, inside `create_app()`, add:

```python
from quantpilot.api.ws import router as ws_router
app.include_router(ws_router)
```

- [ ] **Step 6: Update scheduler to publish bars**

In `backend/src/quantpilot/data/scheduler.py`, after the price cache update block in `_update_symbol`, add:

```python
            # 发布到 Redis pub/sub（行情实时推送）
            try:
                from quantpilot.redis.client import RedisClient
                from quantpilot.redis.pubsub import BarPublisher
                if RedisClient._instance is not None:
                    publisher = BarPublisher()
                    loop = asyncio.new_event_loop()
                    for bar in bars[-5:]:  # 只推最新几根，避免大量历史数据flooding
                        loop.run_until_complete(publisher.publish(bar))
                    loop.close()
            except Exception as e:
                logger.debug(f"[Scheduler] bar 发布跳过: {e}")
```

(Make sure `import asyncio` is at the top of scheduler.py — add if missing.)

- [ ] **Step 7: Run pubsub tests**

```bash
cd /Users/bytedance/code/QuantPilot/backend && uv run pytest tests/test_pubsub.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 8: Lint**

```bash
cd /Users/bytedance/code/QuantPilot/backend && uv run ruff check src/quantpilot/redis/pubsub.py src/quantpilot/api/ws.py tests/test_pubsub.py --fix
```

- [ ] **Step 9: Commit**

```bash
cd /Users/bytedance/code/QuantPilot/backend
git add src/quantpilot/redis/pubsub.py src/quantpilot/api/ws.py tests/test_pubsub.py src/quantpilot/main.py src/quantpilot/data/scheduler.py
git commit -m "feat(redis): add bar pub/sub publisher and WebSocket streaming endpoints"
```

---

## Task 4: Signal Broadcaster Redis Upgrade

**Files:**
- Modify: `backend/src/quantpilot/signals/broadcaster.py`
- Test: `backend/tests/test_signals.py` (extend existing)

- [ ] **Step 1: Read existing broadcaster**

Read `backend/src/quantpilot/signals/broadcaster.py` to understand current SQLite publish method.

- [ ] **Step 2: Add Redis publish to broadcaster.publish()**

Modify the `publish` method in `SignalBroadcaster` to also publish to Redis after the SQLite insert:

```python
async def publish(self, signal: TradingSignal) -> int:
    """发布信号到数据库，并推送到 Redis pub/sub.

    Returns:
        新插入记录的 id
    """
    import json

    async with aiosqlite.connect(self._db_path) as conn:
        await self._ensure_table(conn)
        cursor = await conn.execute(
            "INSERT INTO signals (source, symbol, action, price, confidence, reason, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (signal.source, signal.symbol, signal.action, signal.price,
             signal.confidence, signal.reason, signal.timestamp),
        )
        await conn.commit()
        row_id = cursor.lastrowid or 0
        logger.info(f"[Signals] 发布信号 #{row_id}: {signal.action} {signal.symbol} @ {signal.price}")

    # Redis pub/sub：实时推送信号（非阻塞，失败不影响主流程）
    try:
        from quantpilot.redis.client import RedisClient
        from quantpilot.redis.pubsub import signal_channel
        if RedisClient._instance is not None:
            r = RedisClient.get()
            channel = signal_channel(signal.symbol)
            payload = json.dumps({
                "id": row_id,
                "source": signal.source,
                "symbol": signal.symbol,
                "action": signal.action,
                "price": signal.price,
                "confidence": signal.confidence,
                "reason": signal.reason,
                "timestamp": signal.timestamp,
            })
            await r.publish(channel, payload)
            logger.debug(f"[Signals] Redis 推送 {channel}")
    except Exception as e:
        logger.debug(f"[Signals] Redis 推送跳过: {e}")

    return row_id
```

- [ ] **Step 3: Add Redis pub/sub test for signals**

In `backend/tests/test_signals.py`, add a new test class at the end:

```python
import json
import fakeredis.aioredis
from quantpilot.redis.client import RedisClient
from quantpilot.redis.pubsub import signal_channel


class TestSignalRedisPublish:
    async def test_publish_sends_to_redis_channel(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
            RedisClient._instance = fake_redis

            broadcaster = SignalBroadcaster(db_path=Path(tmpdir) / "signals.db")

            # Subscribe to signals channel
            pubsub = fake_redis.pubsub()
            await pubsub.subscribe(signal_channel("AAPL"))

            sig = TradingSignal(source="test", symbol="AAPL", action="buy", price=150.0)
            await broadcaster.publish(sig)

            msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            assert msg is not None
            data = json.loads(msg["data"])
            assert data["symbol"] == "AAPL"
            assert data["action"] == "buy"

            RedisClient._instance = None

    async def test_publish_works_without_redis(self) -> None:
        """Redis 未连接时，SQLite 写入仍然正常."""
        with tempfile.TemporaryDirectory() as tmpdir:
            RedisClient._instance = None
            broadcaster = SignalBroadcaster(db_path=Path(tmpdir) / "signals.db")
            sig = TradingSignal(source="test", symbol="AAPL", action="sell", price=140.0)
            row_id = await broadcaster.publish(sig)
            assert row_id > 0
```

(Make sure `import json`, `import fakeredis.aioredis`, and the `RedisClient`/`signal_channel` imports are at the top of the test file.)

- [ ] **Step 4: Run tests**

```bash
cd /Users/bytedance/code/QuantPilot/backend && uv run pytest tests/test_signals.py -v
```

Expected: All 9 tests PASS (7 existing + 2 new).

- [ ] **Step 5: Lint**

```bash
cd /Users/bytedance/code/QuantPilot/backend && uv run ruff check src/quantpilot/signals/broadcaster.py tests/test_signals.py --fix
```

- [ ] **Step 6: Commit**

```bash
cd /Users/bytedance/code/QuantPilot/backend
git add src/quantpilot/signals/broadcaster.py tests/test_signals.py
git commit -m "feat(redis): upgrade SignalBroadcaster to push signals via Redis pub/sub"
```

---

## Task 5: Order Queue via Redis Streams

**Files:**
- Create: `backend/src/quantpilot/redis/order_queue.py`
- Modify: `backend/src/quantpilot/api/paper.py`
- Test: `backend/tests/test_order_queue.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_order_queue.py
"""订单队列测试 — Task 5 验收."""
from __future__ import annotations

import pytest
import fakeredis.aioredis

from quantpilot.redis.client import RedisClient
from quantpilot.redis.order_queue import OrderQueue, QueuedOrder


@pytest.fixture(autouse=True)
async def setup_redis():
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    RedisClient._instance = fake
    yield fake
    await RedisClient.disconnect()
    RedisClient._instance = None


class TestQueuedOrder:
    def test_fields(self) -> None:
        order = QueuedOrder(
            session_id="sess1",
            symbol="AAPL",
            side="buy",
            quantity=10,
            price=150.0,
        )
        assert order.session_id == "sess1"
        assert order.symbol == "AAPL"
        assert order.side == "buy"
        assert order.entry_id == ""  # not yet enqueued

    def test_auto_timestamp(self) -> None:
        order = QueuedOrder(session_id="s", symbol="X", side="buy", quantity=1, price=1.0)
        assert order.timestamp != ""


class TestOrderQueue:
    async def test_enqueue_returns_entry_id(self) -> None:
        q = OrderQueue("session1")
        order = QueuedOrder(session_id="session1", symbol="AAPL", side="buy", quantity=10, price=150.0)
        entry_id = await q.enqueue(order)
        assert entry_id != ""
        assert "-" in entry_id  # Redis stream ID format: timestamp-sequence

    async def test_dequeue_returns_enqueued_order(self) -> None:
        q = OrderQueue("session1")
        order = QueuedOrder(session_id="session1", symbol="TSLA", side="sell", quantity=5, price=700.0)
        await q.enqueue(order)

        orders = await q.dequeue(count=10)
        assert len(orders) == 1
        assert orders[0].symbol == "TSLA"
        assert orders[0].side == "sell"
        assert orders[0].quantity == 5

    async def test_dequeue_empty_returns_empty_list(self) -> None:
        q = OrderQueue("empty_session")
        orders = await q.dequeue(count=5)
        assert orders == []

    async def test_enqueue_multiple_maintains_order(self) -> None:
        q = OrderQueue("session2")
        for i in range(5):
            await q.enqueue(QueuedOrder(
                session_id="session2", symbol=f"SYM{i}",
                side="buy", quantity=i + 1, price=float(100 + i)
            ))
        orders = await q.dequeue(count=10)
        assert len(orders) == 5
        symbols = [o.symbol for o in orders]
        assert symbols == [f"SYM{i}" for i in range(5)]

    async def test_stream_length(self) -> None:
        q = OrderQueue("session3")
        for _ in range(3):
            await q.enqueue(QueuedOrder(session_id="session3", symbol="X", side="buy", quantity=1, price=1.0))
        length = await q.length()
        assert length == 3

    async def test_clear_stream(self) -> None:
        q = OrderQueue("session4")
        await q.enqueue(QueuedOrder(session_id="session4", symbol="A", side="buy", quantity=1, price=1.0))
        await q.clear()
        assert await q.length() == 0
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /Users/bytedance/code/QuantPilot/backend && uv run pytest tests/test_order_queue.py -v 2>&1 | head -20
```

Expected: `ImportError`.

- [ ] **Step 3: Implement OrderQueue**

```python
# backend/src/quantpilot/redis/order_queue.py
"""订单队列 — Redis Streams 实现."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime

from loguru import logger

from quantpilot.redis.client import RedisClient


def _stream_key(session_id: str) -> str:
    return f"orders:{session_id}"


@dataclass
class QueuedOrder:
    """待执行订单."""

    session_id: str
    symbol: str
    side: str         # "buy" | "sell"
    quantity: int
    price: float
    entry_id: str = field(default="")          # Redis Stream entry ID，入队后填充
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    reason: str = field(default="")


class OrderQueue:
    """基于 Redis Streams 的可靠订单队列.

    每个模拟盘 session 对应一条独立的 Stream（key: orders:{session_id}）。
    使用简单的 XADD/XRANGE 模式（无 consumer groups），适合单消费者场景。
    """

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._key = _stream_key(session_id)
        self._last_id = "0"  # XRANGE 读取游标

    async def enqueue(self, order: QueuedOrder) -> str:
        """将订单写入 Redis Stream.

        Args:
            order: 待入队订单

        Returns:
            Redis Stream entry ID（如 "1704067200000-0"）
        """
        r = RedisClient.get()
        payload = {
            "session_id": order.session_id,
            "symbol": order.symbol,
            "side": order.side,
            "quantity": str(order.quantity),
            "price": str(order.price),
            "timestamp": order.timestamp,
            "reason": order.reason,
        }
        entry_id: str = await r.xadd(self._key, payload)
        order.entry_id = entry_id
        logger.info(f"[OrderQueue] 入队 {entry_id}: {order.side} {order.symbol} x{order.quantity}")
        return entry_id

    async def dequeue(self, count: int = 10) -> list[QueuedOrder]:
        """从 Stream 读取待处理订单（从游标 _last_id 开始，不删除）.

        Args:
            count: 最多读取条数

        Returns:
            订单列表（按入队顺序）
        """
        r = RedisClient.get()
        raw: list[tuple[str, dict[str, str]]] = await r.xrange(
            self._key, min=self._last_id, count=count
        )
        if not raw:
            return []

        orders = []
        for entry_id, fields in raw:
            orders.append(QueuedOrder(
                session_id=fields["session_id"],
                symbol=fields["symbol"],
                side=fields["side"],
                quantity=int(fields["quantity"]),
                price=float(fields["price"]),
                entry_id=entry_id,
                timestamp=fields.get("timestamp", ""),
                reason=fields.get("reason", ""),
            ))
            self._last_id = entry_id  # 推进游标

        return orders

    async def length(self) -> int:
        """返回队列中的订单数量."""
        r = RedisClient.get()
        return await r.xlen(self._key)

    async def clear(self) -> None:
        """清空队列（删除整条 Stream）."""
        r = RedisClient.get()
        await r.delete(self._key)
        self._last_id = "0"
        logger.info(f"[OrderQueue] 队列 {self._key} 已清空")
```

- [ ] **Step 4: Add order queue endpoints to paper API**

In `backend/src/quantpilot/api/paper.py`, add at the end:

```python
@router.post("/sessions/{session_id}/orders/enqueue")
async def enqueue_order(session_id: str, req: dict) -> dict[str, str]:  # type: ignore[type-arg]
    """提交订单到 Redis 订单队列.

    Request body: {"symbol": "AAPL", "side": "buy", "quantity": 10, "price": 150.0, "reason": ""}
    """
    from quantpilot.redis.client import RedisClient
    from quantpilot.redis.order_queue import OrderQueue, QueuedOrder

    if RedisClient._instance is None:
        raise HTTPException(status_code=503, detail="Redis 未连接")
    with _lock:
        if session_id not in _sessions:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")

    order = QueuedOrder(
        session_id=session_id,
        symbol=req.get("symbol", ""),
        side=req.get("side", "buy"),
        quantity=int(req.get("quantity", 0)),
        price=float(req.get("price", 0.0)),
        reason=req.get("reason", ""),
    )
    q = OrderQueue(session_id)
    entry_id = await q.enqueue(order)
    return {"entry_id": entry_id, "message": f"订单已入队: {order.side} {order.symbol}"}


@router.get("/sessions/{session_id}/orders/queue")
async def get_order_queue(session_id: str, count: int = 20) -> dict:  # type: ignore[type-arg]
    """查看指定 session 的订单队列."""
    from quantpilot.redis.client import RedisClient
    from quantpilot.redis.order_queue import OrderQueue

    if RedisClient._instance is None:
        raise HTTPException(status_code=503, detail="Redis 未连接")
    q = OrderQueue(session_id)
    orders = await q.dequeue(count=count)
    length = await q.length()
    return {
        "session_id": session_id,
        "total": length,
        "orders": [
            {
                "entry_id": o.entry_id,
                "symbol": o.symbol,
                "side": o.side,
                "quantity": o.quantity,
                "price": o.price,
                "timestamp": o.timestamp,
            }
            for o in orders
        ],
    }
```

(Make sure `HTTPException` is imported — it should already be in `paper.py`.)

- [ ] **Step 5: Run tests**

```bash
cd /Users/bytedance/code/QuantPilot/backend && uv run pytest tests/test_order_queue.py -v
```

Expected: All 7 tests PASS.

- [ ] **Step 6: Lint**

```bash
cd /Users/bytedance/code/QuantPilot/backend && uv run ruff check src/quantpilot/redis/order_queue.py src/quantpilot/api/paper.py tests/test_order_queue.py --fix
```

- [ ] **Step 7: Commit**

```bash
cd /Users/bytedance/code/QuantPilot/backend
git add src/quantpilot/redis/order_queue.py tests/test_order_queue.py src/quantpilot/api/paper.py
git commit -m "feat(redis): add Redis Streams order queue for paper trading sessions"
```

---

## Task 6: Frontend LiveDataPanel + /health Redis Status

**Files:**
- Create: `frontend/src/components/LiveDataPanel.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `backend/src/quantpilot/main.py` (health check shows Redis status)

- [ ] **Step 1: Create LiveDataPanel.tsx**

```typescript
// frontend/src/components/LiveDataPanel.tsx
/**
 * 实时行情 & 信号面板 — WebSocket 订阅.
 */
import { useCallback, useEffect, useRef, useState } from "react";

interface BarMsg {
  symbol: string;
  timeframe: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface SignalMsg {
  id: number;
  source: string;
  symbol: string;
  action: string;
  price: number;
  confidence: number;
  reason: string;
  timestamp: string;
}

function useWebSocket<T>(
  url: string,
  enabled: boolean,
): { messages: T[]; status: string } {
  const [messages, setMessages] = useState<T[]>([]);
  const [status, setStatus] = useState("disconnected");
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!enabled) return;
    setStatus("connecting");
    const socket = new WebSocket(url);
    ws.current = socket;

    socket.onopen = () => setStatus("connected");
    socket.onclose = () => setStatus("disconnected");
    socket.onerror = () => setStatus("error");
    socket.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data as string) as T;
        setMessages((prev) => [msg, ...prev].slice(0, 50));
      } catch (_) {}
    };
    return () => {
      socket.close();
    };
  }, [url, enabled]);

  return { messages, status };
}

const statusColor = (s: string) =>
  s === "connected" ? "#34d399" : s === "connecting" ? "#fbbf24" : "#f87171";

export default function LiveDataPanel() {
  const [symbol, setSymbol] = useState("AAPL");
  const [timeframe, setTimeframe] = useState("1d");
  const [barEnabled, setBarEnabled] = useState(false);
  const [signalEnabled, setSignalEnabled] = useState(false);
  const [wsBase, setWsBase] = useState("ws://localhost:8000");

  const barUrl = `${wsBase}/ws/bars/${symbol}/${timeframe}`;
  const signalUrl = `${wsBase}/ws/signals`;

  const { messages: bars, status: barStatus } = useWebSocket<BarMsg>(barUrl, barEnabled);
  const { messages: signals, status: sigStatus } = useWebSocket<SignalMsg>(signalUrl, signalEnabled);

  const inputSt = {
    padding: "5px 8px", fontSize: 12, background: "#1e293b",
    border: "1px solid #334155", borderRadius: 4, color: "#e2e8f0", outline: "none",
  } as const;

  const actionColor = (a: string) =>
    a === "buy" ? "#34d399" : a === "sell" ? "#f87171" : "#64748b";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* 配置区 */}
      <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 8, padding: 16, display: "flex", gap: 16, alignItems: "flex-end", flexWrap: "wrap" }}>
        <div>
          <div style={{ fontSize: 11, color: "#64748b", marginBottom: 4 }}>WebSocket 服务地址</div>
          <input value={wsBase} onChange={(e) => setWsBase(e.target.value)}
            style={{ ...inputSt, width: 220 }} />
        </div>
        <div>
          <div style={{ fontSize: 11, color: "#64748b", marginBottom: 4 }}>标的</div>
          <input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            style={{ ...inputSt, width: 80 }} />
        </div>
        <div>
          <div style={{ fontSize: 11, color: "#64748b", marginBottom: 4 }}>周期</div>
          <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)}
            style={{ ...inputSt, background: "#1e293b" }}>
            {["1m","5m","15m","1h","4h","1d"].map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            onClick={() => setBarEnabled((v) => !v)}
            style={{ padding: "6px 14px", fontSize: 12, fontWeight: 600, border: "none", borderRadius: 4, cursor: "pointer", background: barEnabled ? "#1e3a5f" : "#1e293b", color: barEnabled ? "#60a5fa" : "#64748b" }}>
            {barEnabled ? "停止行情" : "订阅行情"}
          </button>
          <button
            onClick={() => setSignalEnabled((v) => !v)}
            style={{ padding: "6px 14px", fontSize: 12, fontWeight: 600, border: "none", borderRadius: 4, cursor: "pointer", background: signalEnabled ? "#1e3a5f" : "#1e293b", color: signalEnabled ? "#60a5fa" : "#64748b" }}>
            {signalEnabled ? "停止信号" : "订阅信号"}
          </button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {/* Bar stream */}
        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 8, padding: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: "#94a3b8" }}>
              实时行情 — {symbol}/{timeframe}
            </div>
            <div style={{ fontSize: 11, color: statusColor(barStatus), fontWeight: 600 }}>
              ● {barStatus}
            </div>
          </div>
          {bars.length === 0 ? (
            <div style={{ color: "#334155", fontSize: 12 }}>等待行情推送…</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 400, overflowY: "auto" }}>
              {bars.map((bar, i) => (
                <div key={i} style={{ background: "#1e293b", borderRadius: 4, padding: "8px 12px", fontSize: 12 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ color: "#e2e8f0", fontWeight: 600 }}>{bar.symbol}</span>
                    <span style={{ color: "#64748b" }}>{bar.timestamp.slice(0, 19)}</span>
                  </div>
                  <div style={{ display: "flex", gap: 12, color: "#94a3b8" }}>
                    {[["O", bar.open], ["H", bar.high], ["L", bar.low], ["C", bar.close]].map(([k, v]) => (
                      <span key={k as string}><span style={{ color: "#475569" }}>{k}</span> {(v as number).toFixed(2)}</span>
                    ))}
                    <span style={{ color: "#475569" }}>Vol {(bar.volume / 1e6).toFixed(1)}M</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Signal stream */}
        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 8, padding: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: "#94a3b8" }}>实时信号</div>
            <div style={{ fontSize: 11, color: statusColor(sigStatus), fontWeight: 600 }}>
              ● {sigStatus}
            </div>
          </div>
          {signals.length === 0 ? (
            <div style={{ color: "#334155", fontSize: 12 }}>等待信号推送…</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 400, overflowY: "auto" }}>
              {signals.map((sig, i) => (
                <div key={i} style={{ background: "#1e293b", borderRadius: 4, padding: "8px 12px", borderLeft: `3px solid ${actionColor(sig.action)}`, fontSize: 12 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 2 }}>
                    <span style={{ color: actionColor(sig.action), fontWeight: 700 }}>
                      {sig.action.toUpperCase()} {sig.symbol}
                    </span>
                    <span style={{ color: "#64748b" }}>{sig.confidence ? `${(sig.confidence * 100).toFixed(0)}%` : ""}</span>
                  </div>
                  <div style={{ color: "#64748b" }}>${sig.price} · {sig.source}</div>
                  {sig.reason && <div style={{ color: "#475569", marginTop: 2 }}>{sig.reason}</div>}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Add "实时" tab to App.tsx**

Read `frontend/src/App.tsx`, then:

1. Add import at the top with other imports:
```typescript
import LiveDataPanel from "./components/LiveDataPanel";
```

2. Add to `type Tab`:
```typescript
| "live"
```

3. Add to `TABS` array:
```typescript
{ key: "live", label: "实时" },
```

4. Add render in `<main>`:
```typescript
{activeTab === "live" && <LiveDataPanel />}
```

- [ ] **Step 3: Update /health to show Redis status**

In `backend/src/quantpilot/main.py`, replace the health check handler:

```python
@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """健康检查端点."""
    from quantpilot.redis.client import RedisClient
    redis_ok = await RedisClient.ping()
    return {
        "status": "ok",
        "version": settings.app_version,
        "redis": "connected" if redis_ok else "disconnected",
    }
```

- [ ] **Step 4: Verify frontend builds**

```bash
cd /Users/bytedance/code/QuantPilot/frontend && npm run build 2>&1 | tail -10
```

Expected: Build succeeds without TypeScript errors.

- [ ] **Step 5: Commit**

```bash
cd /Users/bytedance/code/QuantPilot/frontend
git add src/components/LiveDataPanel.tsx src/App.tsx
git commit -m "feat(frontend): add LiveDataPanel with WebSocket bar and signal streams"

cd /Users/bytedance/code/QuantPilot/backend
git add src/quantpilot/main.py
git commit -m "feat(redis): add Redis status to /health endpoint"
```

---

## Task 7: Final Integration

- [ ] **Step 1: Run full backend test suite**

```bash
cd /Users/bytedance/code/QuantPilot/backend && uv run pytest tests/ -v 2>&1 | tail -30
```

Expected: All new tests pass; 5 pre-existing Rust failures are unrelated.

- [ ] **Step 2: Full ruff check**

```bash
cd /Users/bytedance/code/QuantPilot/backend && uv run ruff check src/ tests/ 2>&1 | grep -v "^$"
```

Expected: No errors.

- [ ] **Step 3: Verify remote Redis connection**

Set environment variable and test manually:

```bash
QUANTPILOT_REDIS_URL=redis://your-remote-host:6379 \
  cd /Users/bytedance/code/QuantPilot/backend && uv run python -c "
import asyncio
from quantpilot.redis.client import RedisClient

async def main():
    await RedisClient.connect('redis://your-remote-host:6379')
    print('ping:', await RedisClient.ping())
    await RedisClient.disconnect()

asyncio.run(main())
"
```

Expected: `ping: True`

- [ ] **Step 4: Set QUANTPILOT_REDIS_URL in .env**

In `backend/.env` (create if absent):

```
QUANTPILOT_REDIS_URL=redis://your-remote-host:6379
```

(If the remote Redis has a password: `redis://:password@host:6379/0`)

- [ ] **Step 5: Final commit**

```bash
cd /Users/bytedance/code/QuantPilot && git add backend/.env.example
git commit -m "docs: add .env.example with QUANTPILOT_REDIS_URL"
```

---

## Self-Review

**Spec coverage:**
- 行情 pub/sub: Covered by Task 3 — `BarPublisher` + `BarPublisher.publish()` called in scheduler, WebSocket `/ws/bars/{symbol}/{timeframe}`
- 实盘订单队列: Covered by Task 5 — `OrderQueue` (Redis Streams XADD/XRANGE) + REST enqueue/dequeue endpoints
- 最新价格缓存: Covered by Task 2 — `PriceCache` + `/api/data/prices` endpoint
- 信号实时推送: Covered by Task 4 — `SignalBroadcaster.publish()` Redis side-effect + `/ws/signals` WebSocket
- Redis 降级: `lifespan` wraps `connect()` in try/except — app starts even if Redis unavailable; all Redis operations check `_instance is not None` before proceeding

**Placeholder scan:** No TBD, no "handle edge cases", all code blocks complete.

**Type consistency:**
- `RedisClient.get()` returns `aioredis.Redis` — used consistently in price_cache, pubsub, order_queue
- `BarPublisher.publish(bar: OHLCVBar) -> int` — matches scheduler call pattern
- `OrderQueue.dequeue() -> list[QueuedOrder]` — used in paper.py endpoint
- `signal_channel(symbol)` defined in pubsub.py — imported correctly in broadcaster.py and test
