"""信号广播器 — SQLite 持久化交易信号."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiosqlite
from loguru import logger

_DEFAULT_DB = Path.home() / ".quantpilot" / "signals.db"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS signals (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    source    TEXT NOT NULL,
    symbol    TEXT NOT NULL,
    action    TEXT NOT NULL,
    price     REAL NOT NULL,
    confidence REAL,
    reason    TEXT,
    timestamp TEXT NOT NULL
)
"""


@dataclass
class TradingSignal:
    """交易信号数据模型."""

    source: str
    symbol: str
    action: str
    price: float
    confidence: float = 0.0
    reason: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class SignalBroadcaster:
    """发布交易信号到 SQLite 信号库."""

    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path or _DEFAULT_DB
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

    async def _ensure_table(self, conn: aiosqlite.Connection) -> None:
        await conn.execute(_CREATE_TABLE)
        await conn.commit()

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

    async def get_feed(
        self,
        symbol: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """查询信号列表（按时间倒序）."""
        async with aiosqlite.connect(self._db_path) as conn:
            await self._ensure_table(conn)
            conn.row_factory = aiosqlite.Row
            if symbol:
                cursor = await conn.execute(
                    "SELECT * FROM signals WHERE symbol=? ORDER BY id DESC LIMIT ?",
                    (symbol, limit),
                )
            else:
                cursor = await conn.execute(
                    "SELECT * FROM signals ORDER BY id DESC LIMIT ?", (limit,)
                )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
