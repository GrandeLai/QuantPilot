"""信号订阅器 — 读取信号推送."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from quantpilot_quant.signals.broadcaster import _DEFAULT_DB, SignalBroadcaster


class SignalSubscriber:
    """从信号库读取最新信号（跟单方）."""

    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path or _DEFAULT_DB

    async def get_latest(
        self,
        symbol: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """获取最新信号."""
        broadcaster = SignalBroadcaster(db_path=self._db_path)
        return await broadcaster.get_feed(symbol=symbol, limit=limit)
