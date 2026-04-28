"""订单队列 — Redis Streams 实现."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from loguru import logger

from quantpilot_common.redis.client import RedisClient


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
        entry_id: str = await r.xadd(self._key, payload)  # type: ignore[arg-type, misc]
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
