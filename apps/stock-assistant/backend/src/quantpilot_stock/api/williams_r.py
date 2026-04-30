"""Williams %R API — Phase F.44.

GET /api/williams-r?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.williams_r.engine import (
    WilliamsRData,
    WilliamsRSignal,
    compute_williams_r,
)

router = APIRouter(tags=["williams_r"])


class WilliamsRResponse(BaseModel):
    ticker: str
    williams_r: float | None
    prev_williams_r: float | None
    wr_direction: str
    overbought: bool
    oversold: bool
    wr_score: float
    signal: WilliamsRSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: WilliamsRData) -> WilliamsRResponse:
    return WilliamsRResponse(
        ticker=data.ticker,
        williams_r=data.williams_r,
        prev_williams_r=data.prev_williams_r,
        wr_direction=data.wr_direction,
        overbought=data.overbought,
        oversold=data.oversold,
        wr_score=data.wr_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/williams-r", response_model=WilliamsRResponse)
async def get_williams_r(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> WilliamsRResponse:
    """Return Williams %R data for the given ticker."""
    data = compute_williams_r(ticker.upper())
    return _to_response(data)
