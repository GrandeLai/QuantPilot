"""Ultimate Oscillator API — Phase F.54.

GET /api/ultimate-osc?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.ultimate_osc.engine import (
    UltimateOscData,
    UltimateOscSignal,
    compute_ultimate_osc,
)

router = APIRouter(tags=["ultimate_osc"])


class UltimateOscResponse(BaseModel):
    ticker: str
    uo_value: float | None
    uo_overbought: bool
    uo_oversold: bool
    uo_score: float
    signal: UltimateOscSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: UltimateOscData) -> UltimateOscResponse:
    return UltimateOscResponse(
        ticker=data.ticker,
        uo_value=data.uo_value,
        uo_overbought=data.uo_overbought,
        uo_oversold=data.uo_oversold,
        uo_score=data.uo_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/ultimate-osc", response_model=UltimateOscResponse)
async def get_ultimate_osc(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> UltimateOscResponse:
    """Return Ultimate Oscillator data for the given ticker."""
    data = compute_ultimate_osc(ticker.upper())
    return _to_response(data)
