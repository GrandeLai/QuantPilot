"""信号广播 API.

端点:
  POST /signals/publish   发布交易信号
  GET  /signals/feed      查询信号列表
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from quantpilot.signals.broadcaster import SignalBroadcaster, TradingSignal

router = APIRouter(prefix="/signals", tags=["信号广播"])

_broadcaster = SignalBroadcaster()


class PublishRequest(BaseModel):
    source: str
    symbol: str
    action: str
    price: float
    confidence: float = 0.0
    reason: str = ""


@router.post("/publish")
async def publish_signal(req: PublishRequest) -> dict[str, Any]:
    """发布交易信号到信号库."""
    signal = TradingSignal(
        source=req.source,
        symbol=req.symbol,
        action=req.action,
        price=req.price,
        confidence=req.confidence,
        reason=req.reason,
    )
    signal_id = await _broadcaster.publish(signal)
    return {"id": signal_id, "message": f"信号已发布: {req.action} {req.symbol}"}


@router.get("/feed")
async def get_feed(symbol: str | None = None, limit: int = 50) -> dict[str, Any]:
    """查询信号列表."""
    signals = await _broadcaster.get_feed(symbol=symbol, limit=limit)
    return {"signals": signals, "count": len(signals)}
