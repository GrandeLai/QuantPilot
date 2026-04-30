"""TSI API — Phase F.57.

GET /api/tsi?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.tsi.engine import (
    TSIData,
    TSISignal,
    compute_tsi,
)

router = APIRouter(tags=["tsi"])


class TSIResponse(BaseModel):
    ticker: str
    tsi_value: float | None
    signal_line: float | None
    tsi_positive: bool
    tsi_above_signal: bool
    tsi_score: float
    signal: TSISignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: TSIData) -> TSIResponse:
    return TSIResponse(
        ticker=data.ticker,
        tsi_value=data.tsi_value,
        signal_line=data.signal_line,
        tsi_positive=data.tsi_positive,
        tsi_above_signal=data.tsi_above_signal,
        tsi_score=data.tsi_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/tsi", response_model=TSIResponse)
async def get_tsi(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> TSIResponse:
    """Return TSI (True Strength Index) data for the given ticker."""
    data = compute_tsi(ticker.upper())
    return _to_response(data)
