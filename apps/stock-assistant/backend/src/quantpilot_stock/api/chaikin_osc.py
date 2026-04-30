"""Chaikin Oscillator API — Phase F.61.

GET /api/chaikin_osc?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.chaikin_osc.engine import (
    ChaikinOscData,
    ChaikinOscSignal,
    compute_chaikin_osc,
)

router = APIRouter(tags=["chaikin_osc"])


class ChaikinOscResponse(BaseModel):
    ticker: str
    chaikin_osc: float | None
    osc_positive: bool | None
    chaikin_score: float
    signal: ChaikinOscSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: ChaikinOscData) -> ChaikinOscResponse:
    return ChaikinOscResponse(
        ticker=data.ticker,
        chaikin_osc=data.chaikin_osc,
        osc_positive=data.osc_positive,
        chaikin_score=data.chaikin_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/chaikin_osc", response_model=ChaikinOscResponse)
async def get_chaikin_osc(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> ChaikinOscResponse:
    """Return Chaikin Oscillator data for the given ticker."""
    data = compute_chaikin_osc(ticker.upper())
    return _to_response(data)
