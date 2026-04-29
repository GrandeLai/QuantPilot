"""Stochastic Oscillator API — Phase F.40.

GET /api/stochastic?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.stochastic.engine import (
    StochasticData,
    StochasticSignal,
    compute_stochastic,
)

router = APIRouter(tags=["stochastic"])


class StochasticResponse(BaseModel):
    ticker: str
    k: float | None
    d: float | None
    prev_k: float | None
    prev_d: float | None
    overbought: bool
    oversold: bool
    k_above_d: bool
    recent_bull_cross: bool
    recent_bear_cross: bool
    stoch_score: float
    signal: StochasticSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: StochasticData) -> StochasticResponse:
    return StochasticResponse(
        ticker=data.ticker,
        k=data.k,
        d=data.d,
        prev_k=data.prev_k,
        prev_d=data.prev_d,
        overbought=data.overbought,
        oversold=data.oversold,
        k_above_d=data.k_above_d,
        recent_bull_cross=data.recent_bull_cross,
        recent_bear_cross=data.recent_bear_cross,
        stoch_score=data.stoch_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/stochastic", response_model=StochasticResponse)
async def get_stochastic(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> StochasticResponse:
    """Return Stochastic Oscillator data for the given ticker."""
    data = compute_stochastic(ticker.upper())
    return _to_response(data)
