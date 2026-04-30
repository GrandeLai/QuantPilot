"""Elder Impulse System API — Phase F.80.

GET /api/elder_impulse?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.elder_impulse.engine import (
    ImpulseColor,
    ImpulseData,
    ImpulseSignal,
    compute_impulse,
)

router = APIRouter(tags=["elder_impulse"])


class ImpulseResponse(BaseModel):
    ticker: str
    ema13: float | None
    macd_hist: float | None
    impulse_color: ImpulseColor | None
    ema_rising: bool | None
    hist_rising: bool | None
    impulse_score: float
    signal: ImpulseSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: ImpulseData) -> ImpulseResponse:
    return ImpulseResponse(
        ticker=data.ticker,
        ema13=data.ema13,
        macd_hist=data.macd_hist,
        impulse_color=data.impulse_color,
        ema_rising=data.ema_rising,
        hist_rising=data.hist_rising,
        impulse_score=data.impulse_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/elder_impulse", response_model=ImpulseResponse)
async def get_elder_impulse(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> ImpulseResponse:
    """Return Elder Impulse System data for the given ticker."""
    data = compute_impulse(ticker.upper())
    return _to_response(data)
