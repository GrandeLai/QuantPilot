"""CMO API — Phase F.65.

GET /api/cmo?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.cmo.engine import (
    CMOData,
    CMOSignal,
    compute_cmo,
)

router = APIRouter(tags=["cmo"])


class CMOResponse(BaseModel):
    ticker: str
    cmo_value: float | None
    signal_value: float | None
    cmo_above_signal: bool | None
    cmo_positive: bool | None
    cmo_score: float
    signal: CMOSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: CMOData) -> CMOResponse:
    return CMOResponse(
        ticker=data.ticker,
        cmo_value=data.cmo_value,
        signal_value=data.signal_value,
        cmo_above_signal=data.cmo_above_signal,
        cmo_positive=data.cmo_positive,
        cmo_score=data.cmo_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/cmo", response_model=CMOResponse)
async def get_cmo(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> CMOResponse:
    """Return Chande Momentum Oscillator data for the given ticker."""
    data = compute_cmo(ticker.upper())
    return _to_response(data)
