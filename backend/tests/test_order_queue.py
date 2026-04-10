"""订单队列测试 — Task 5 验收."""
from __future__ import annotations

import fakeredis.aioredis
import pytest

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
