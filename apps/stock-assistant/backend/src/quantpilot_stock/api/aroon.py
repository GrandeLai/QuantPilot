"""Aroon Indicator API — Phase F.53.

GET /api/aroon?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.aroon.engine import (
    AroonData,
    AroonSignal,
    compute_aroon,
)

router = APIRouter(tags=["aroon"])


class AroonResponse(BaseModel):
    ticker: str
    aroon_up: float | None
    aroon_down: float | None
    aroon_oscillator: float | None
    aroon_bullish: bool
    aroon_score: float
    signal: AroonSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: AroonData) -> AroonResponse:
    return AroonResponse(
        ticker=data.ticker,
        aroon_up=data.aroon_up,
        aroon_down=data.aroon_down,
        aroon_oscillator=data.aroon_oscillator,
        aroon_bullish=data.aroon_bullish,
        aroon_score=data.aroon_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/aroon", response_model=AroonResponse)
async def get_aroon(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> AroonResponse:
    """Return Aroon Indicator data for the given ticker."""
    data = compute_aroon(ticker.upper())
    return _to_response(data)
