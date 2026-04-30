"""Stochastic RSI API — F.83.

GET /api/stoch_rsi?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.stoch_rsi.engine import (
    StochRSIData,
    StochRSISignal,
    compute_stoch_rsi,
)

router = APIRouter(tags=["stoch_rsi"])


class StochRSIResponse(BaseModel):
    ticker: str
    k_value: float | None
    d_value: float | None
    stoch_rsi_score: float
    signal: StochRSISignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: StochRSIData) -> StochRSIResponse:
    return StochRSIResponse(
        ticker=data.ticker,
        k_value=data.k_value,
        d_value=data.d_value,
        stoch_rsi_score=data.stoch_rsi_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/stoch_rsi", response_model=StochRSIResponse)
async def get_stoch_rsi(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> StochRSIResponse:
    """Return Stochastic RSI data for the given ticker."""
    data = compute_stoch_rsi(ticker.upper())
    return _to_response(data)
