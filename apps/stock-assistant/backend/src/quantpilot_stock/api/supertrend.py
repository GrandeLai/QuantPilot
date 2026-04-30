"""Supertrend API — Phase F.55.

GET /api/supertrend?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.supertrend.engine import (
    SupertrendData,
    SupertrendSignal,
    compute_supertrend,
)

router = APIRouter(tags=["supertrend"])


class SupertrendResponse(BaseModel):
    ticker: str
    supertrend_value: float | None
    distance_pct: float | None
    supertrend_bullish: bool
    supertrend_score: float
    signal: SupertrendSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: SupertrendData) -> SupertrendResponse:
    return SupertrendResponse(
        ticker=data.ticker,
        supertrend_value=data.supertrend_value,
        distance_pct=data.distance_pct,
        supertrend_bullish=data.supertrend_bullish,
        supertrend_score=data.supertrend_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/supertrend", response_model=SupertrendResponse)
async def get_supertrend(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> SupertrendResponse:
    """Return Supertrend data for the given ticker."""
    data = compute_supertrend(ticker.upper())
    return _to_response(data)
