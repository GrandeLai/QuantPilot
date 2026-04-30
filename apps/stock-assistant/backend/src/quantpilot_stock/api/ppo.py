"""PPO API — Phase F.66.

GET /api/ppo?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.ppo.engine import (
    PPOData,
    PPOSignal,
    compute_ppo,
)

router = APIRouter(tags=["ppo"])


class PPOResponse(BaseModel):
    ticker: str
    ppo_value: float | None
    signal_value: float | None
    histogram: float | None
    ppo_above_signal: bool | None
    ppo_positive: bool | None
    ppo_score: float
    signal: PPOSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: PPOData) -> PPOResponse:
    return PPOResponse(
        ticker=data.ticker,
        ppo_value=data.ppo_value,
        signal_value=data.signal_value,
        histogram=data.histogram,
        ppo_above_signal=data.ppo_above_signal,
        ppo_positive=data.ppo_positive,
        ppo_score=data.ppo_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/ppo", response_model=PPOResponse)
async def get_ppo(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> PPOResponse:
    """Return Percentage Price Oscillator data for the given ticker."""
    data = compute_ppo(ticker.upper())
    return _to_response(data)
