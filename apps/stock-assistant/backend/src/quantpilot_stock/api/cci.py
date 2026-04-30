"""CCI API — Phase F.45.

GET /api/cci?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.cci.engine import (
    CCIData,
    CCISignal,
    compute_cci,
)

router = APIRouter(tags=["cci"])


class CCIResponse(BaseModel):
    ticker: str
    cci: float | None
    prev_cci: float | None
    cci_direction: str
    overbought: bool
    oversold: bool
    cci_score: float
    signal: CCISignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: CCIData) -> CCIResponse:
    return CCIResponse(
        ticker=data.ticker,
        cci=data.cci,
        prev_cci=data.prev_cci,
        cci_direction=data.cci_direction,
        overbought=data.overbought,
        oversold=data.oversold,
        cci_score=data.cci_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/cci", response_model=CCIResponse)
async def get_cci(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> CCIResponse:
    """Return CCI data for the given ticker."""
    data = compute_cci(ticker.upper())
    return _to_response(data)
