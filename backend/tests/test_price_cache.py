"""最新价格缓存测试 — Task 2 验收."""
from __future__ import annotations

import fakeredis.aioredis
import pytest

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
