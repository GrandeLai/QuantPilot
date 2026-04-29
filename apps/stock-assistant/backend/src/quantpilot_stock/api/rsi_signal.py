"""RSI Divergence Signal API — Phase F.39.

GET /api/rsi-signal?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.rsi_signal.engine import (
    RSIData,
    RSISignal,
    compute_rsi_signal,
)

router = APIRouter(tags=["rsi-signal"])


class RSIResponse(BaseModel):
    ticker: str
    rsi: float | None
    prev_rsi: float | None
    rsi_direction: str
    overbought: bool
    oversold: bool
    bullish_divergence: bool
    bearish_divergence: bool
    rsi_score: float
    signal: RSISignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: RSIData) -> RSIResponse:
    return RSIResponse(
        ticker=data.ticker,
        rsi=data.rsi,
        prev_rsi=data.prev_rsi,
        rsi_direction=data.rsi_direction,
        overbought=data.overbought,
        oversold=data.oversold,
        bullish_divergence=data.bullish_divergence,
        bearish_divergence=data.bearish_divergence,
        rsi_score=data.rsi_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/rsi-signal", response_model=RSIResponse)
async def get_rsi_signal(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> RSIResponse:
    """Return RSI divergence signal data for the given ticker."""
    data = compute_rsi_signal(ticker.upper())
    return _to_response(data)
