"""信号广播 API.

端点:
  POST /signals/publish         发布交易信号（经滚动分位数过滤后入库）
  GET  /signals/feed            查询信号列表
  GET  /signals/filter/stats    查看过滤器缓冲区统计
  POST /signals/filter/reset    重置过滤器缓冲区
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_common.config import get_settings
from quantpilot_quant.signals.broadcaster import SignalBroadcaster, TradingSignal
from quantpilot_quant.signals.quantile_filter import RollingQuantileFilter

router = APIRouter(prefix="/signals", tags=["信号广播"])

_settings = get_settings()
_quantile_filter = RollingQuantileFilter(
    window=_settings.signal_filter_window,
    quantile=_settings.signal_filter_quantile,
    min_periods=_settings.signal_filter_min_periods,
)
_broadcaster = SignalBroadcaster(quantile_filter=_quantile_filter)


class PublishRequest(BaseModel):
    source: str
    symbol: str
    action: str
    price: float
    confidence: float = 0.0
    reason: str = ""


@router.post("/publish")
async def publish_signal(req: PublishRequest) -> dict[str, Any]:
    """发布交易信号到信号库.

    信号经 RollingQuantileFilter 过滤后写入 SQLite：
    - 通过过滤：action 保持原样；
    - 未通过：action 改为 ``"hold"``，reason 附加过滤说明。
    所有信号均完整存储（含被过滤的），以便回溯分析。
    """
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


@router.get("/filter/stats")
def get_filter_stats(
    symbol: str = Query(..., description="交易对，如 BTC-USDT"),
    source: str = Query(..., description="信号来源，如 lgbm_strategy"),
) -> dict[str, Any]:
    """查看指定 (symbol, source) 的过滤器缓冲区统计信息."""
    stats = _quantile_filter.buffer_stats(symbol=symbol, source=source)
    return {
        "symbol": symbol,
        "source": source,
        "filter_window": _quantile_filter.window,
        "filter_quantile": _quantile_filter.quantile,
        "filter_min_periods": _quantile_filter.min_periods,
        "buffer_stats": stats,
    }


@router.post("/filter/reset")
def reset_filter(
    symbol: str | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    """重置过滤器缓冲区（清空滚动历史）.

    - 不传参数：清空所有缓冲区；
    - 只传 symbol：清空该品种所有来源；
    - 同时传 symbol + source：只清空指定缓冲区。
    """
    _quantile_filter.reset(symbol=symbol, source=source)
    key = f"{symbol}/{source}" if symbol and source else symbol or source or "全部"
    return {"message": f"已重置缓冲区: {key}"}

