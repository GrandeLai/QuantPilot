"""Choppiness Index API — Phase F.79.

GET /api/choppiness?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.choppiness.engine import (
    CHOPData,
    CHOPSignal,
    compute_chop,
)

router = APIRouter(tags=["choppiness"])


class CHOPResponse(BaseModel):
    ticker: str
    chop_value: float | None
    is_trending: bool | None
    price_above_sma: bool | None
    chop_score: float
    signal: CHOPSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: CHOPData) -> CHOPResponse:
    return CHOPResponse(
        ticker=data.ticker,
        chop_value=data.chop_value,
        is_trending=data.is_trending,
        price_above_sma=data.price_above_sma,
        chop_score=data.chop_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/choppiness", response_model=CHOPResponse)
async def get_choppiness(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> CHOPResponse:
    """Return Choppiness Index data for the given ticker."""
    data = compute_chop(ticker.upper())
    return _to_response(data)
