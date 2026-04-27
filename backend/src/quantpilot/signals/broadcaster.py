"""信号广播器 — SQLite 持久化交易信号."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import aiosqlite
from loguru import logger

if TYPE_CHECKING:
    from quantpilot.signals.quantile_filter import RollingQuantileFilter

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
    """发布交易信号到 SQLite 信号库.

    Parameters
    ----------
    db_path:
        SQLite 数据库路径，默认 ``~/.quantpilot/signals.db``。
    quantile_filter:
        可选的滚动分位数过滤器（``RollingQuantileFilter`` 实例）。
        注入后，每次 ``publish()`` 都会先通过过滤器，低于阈值的信号
        ``action`` 字段被改写为 ``"hold"``，并在 ``reason`` 字段中附加
        过滤原因，然后再持久化 / 推送 Redis。这样所有信号仍完整记录，
        便于事后分析过滤效果，同时下游消费者只需检查 ``action != "hold"``
        即可排除观望信号。

    典型用法::

        from quantpilot.signals.quantile_filter import RollingQuantileFilter
        from quantpilot.signals.broadcaster import SignalBroadcaster

        broadcaster = SignalBroadcaster(
            quantile_filter=RollingQuantileFilter(window=20, quantile=0.75)
        )
    """

    def __init__(
        self,
        db_path: Path | None = None,
        quantile_filter: RollingQuantileFilter | None = None,
    ) -> None:
        self._db_path = db_path or _DEFAULT_DB
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._quantile_filter = quantile_filter

    async def _ensure_table(self, conn: aiosqlite.Connection) -> None:
        await conn.execute(_CREATE_TABLE)
        await conn.commit()

    async def publish(self, signal: TradingSignal) -> int:
        """发布信号到数据库，并推送到 Redis pub/sub.

        若注入了 ``quantile_filter``，信号在持久化前先经过滚动分位数过滤：
        - 通过：原样发布；
        - 未通过：``action`` 改为 ``"hold"``，``reason`` 附加过滤说明，
          仍完整写入 SQLite（便于回溯分析），Redis 推送同样更新后的信号。

        Returns:
            新插入记录的 id
        """
        import json

        # ── 滚动分位数过滤 ─────────────────────────────────────────────────
        if self._quantile_filter is not None:
            result = self._quantile_filter.filter(
                symbol=signal.symbol,
                source=signal.source,
                confidence=signal.confidence,
                action=signal.action,
            )
            if not result.passed:
                # 改写 action 并追加过滤原因，其余字段不变
                signal = TradingSignal(
                    source=signal.source,
                    symbol=signal.symbol,
                    action=result.filtered_action,   # "hold"
                    price=signal.price,
                    confidence=signal.confidence,
                    reason=f"{signal.reason} | {result.reason}".lstrip(" | "),
                    timestamp=signal.timestamp,
                )
                logger.info(
                    "[QuantileFilter] {}/{} 信号被过滤 → hold | {}",
                    signal.symbol, signal.source, result.reason,
                )
        # ─────────────────────────────────────────────────────────────────

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
            from quantpilot_common.redis.client import RedisClient
            from quantpilot_common.redis.pubsub import signal_channel
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
