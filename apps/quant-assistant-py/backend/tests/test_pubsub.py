"""行情 Pub/Sub 测试 — Task 3 验收."""
from __future__ import annotations

import json
from datetime import UTC, datetime

import fakeredis.aioredis
import pytest

from quantpilot_common.data.models import OHLCVBar
from quantpilot_common.redis.client import RedisClient
from quantpilot_common.redis.pubsub import BarPublisher, bar_channel


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
        # Drain subscribe confirmation
        _ = await pubsub.get_message(timeout=0.1)

        await publisher.publish(bar)

        # Read the published message
        msg = await pubsub.get_message(timeout=1.0)
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
        # Drain subscribe confirmation
        _ = await pubsub.get_message(timeout=0.1)

        await publisher.publish(bar)

        msg = await pubsub.get_message(timeout=1.0)
        assert msg is not None
        data = json.loads(msg["data"])
        required_fields = {"symbol", "timeframe", "timestamp", "open", "high", "low", "close", "volume"}
        assert required_fields.issubset(set(data.keys()))
