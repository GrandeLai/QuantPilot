"""信号广播测试 — T-4.4 验收."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import fakeredis.aioredis

from quantpilot_common.redis.client import RedisClient
from quantpilot_common.redis.pubsub import signal_channel
from quantpilot.signals.broadcaster import SignalBroadcaster, TradingSignal
from quantpilot.signals.subscriber import SignalSubscriber


def _make_signal(symbol: str = "AAPL", action: str = "buy", price: float = 150.0) -> TradingSignal:
    return TradingSignal(
        source="test_strategy",
        symbol=symbol,
        action=action,
        price=price,
        confidence=0.85,
        reason="MA crossover",
    )


class TestTradingSignal:
    def test_fields(self) -> None:
        sig = _make_signal()
        assert sig.symbol == "AAPL"
        assert sig.action == "buy"
        assert sig.confidence == 0.85

    def test_auto_timestamp(self) -> None:
        sig = _make_signal()
        assert sig.timestamp != ""


class TestSignalBroadcaster:
    async def test_publish_and_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            broadcaster = SignalBroadcaster(db_path=Path(tmpdir) / "signals.db")
            await broadcaster.publish(_make_signal())
            signals = await broadcaster.get_feed(limit=10)
            assert len(signals) == 1
            assert signals[0]["symbol"] == "AAPL"

    async def test_publish_multiple(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            broadcaster = SignalBroadcaster(db_path=Path(tmpdir) / "signals.db")
            for i in range(5):
                await broadcaster.publish(_make_signal(symbol=f"SYM{i}"))
            feed = await broadcaster.get_feed(limit=10)
            assert len(feed) == 5

    async def test_get_feed_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            broadcaster = SignalBroadcaster(db_path=Path(tmpdir) / "signals.db")
            for _i in range(10):
                await broadcaster.publish(_make_signal())
            feed = await broadcaster.get_feed(limit=3)
            assert len(feed) == 3

    async def test_filter_by_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            broadcaster = SignalBroadcaster(db_path=Path(tmpdir) / "signals.db")
            await broadcaster.publish(_make_signal(symbol="AAPL"))
            await broadcaster.publish(_make_signal(symbol="GOOG"))
            feed = await broadcaster.get_feed(symbol="AAPL")
            assert all(s["symbol"] == "AAPL" for s in feed)


class TestSignalSubscriber:
    async def test_subscribe_receives_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "signals.db"
            broadcaster = SignalBroadcaster(db_path=db_path)
            subscriber = SignalSubscriber(db_path=db_path)

            await broadcaster.publish(_make_signal(symbol="TSLA"))
            signals = await subscriber.get_latest(limit=5)
            assert len(signals) >= 1
            assert any(s["symbol"] == "TSLA" for s in signals)


class TestSignalRedisPublish:
    async def test_publish_sends_to_redis_channel(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
            RedisClient._instance = fake_redis

            broadcaster = SignalBroadcaster(db_path=Path(tmpdir) / "signals.db")

            # Subscribe to signals channel
            pubsub = fake_redis.pubsub()
            await pubsub.subscribe(signal_channel("AAPL"))
            # Drain subscribe confirmation
            _ = await pubsub.get_message(timeout=0.1)

            sig = TradingSignal(source="test", symbol="AAPL", action="buy", price=150.0)
            await broadcaster.publish(sig)

            msg = await pubsub.get_message(timeout=1.0)
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
