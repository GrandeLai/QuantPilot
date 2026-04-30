"""STC API — Phase F.71.

GET /api/stc?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.stc.engine import (
    STCData,
    STCSignal,
    compute_stc,
)

router = APIRouter(tags=["stc"])


class STCResponse(BaseModel):
    ticker: str
    stc_value: float | None
    stc_above_buy: bool | None
    stc_rising: bool | None
    stc_score: float
    signal: STCSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: STCData) -> STCResponse:
    return STCResponse(
        ticker=data.ticker,
        stc_value=data.stc_value,
        stc_above_buy=data.stc_above_buy,
        stc_rising=data.stc_rising,
        stc_score=data.stc_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/stc", response_model=STCResponse)
async def get_stc(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> STCResponse:
    """Return Schaff Trend Cycle data for the given ticker."""
    data = compute_stc(ticker.upper())
    return _to_response(data)
