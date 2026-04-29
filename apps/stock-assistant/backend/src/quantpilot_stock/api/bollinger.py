"""Bollinger Band API — Phase F.38.

GET /api/bollinger?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.bollinger.engine import (
    BBSignal,
    BollingerData,
    compute_bollinger,
)

router = APIRouter(tags=["bollinger"])


class BollingerResponse(BaseModel):
    ticker: str
    price: float | None
    middle: float | None
    upper: float | None
    lower: float | None
    bandwidth: float | None
    pct_b: float | None
    bandwidth_percentile: float | None
    squeeze_active: bool
    bb_score: float
    signal: BBSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: BollingerData) -> BollingerResponse:
    return BollingerResponse(
        ticker=data.ticker,
        price=data.price,
        middle=data.middle,
        upper=data.upper,
        lower=data.lower,
        bandwidth=data.bandwidth,
        pct_b=data.pct_b,
        bandwidth_percentile=data.bandwidth_percentile,
        squeeze_active=data.squeeze_active,
        bb_score=data.bb_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/bollinger", response_model=BollingerResponse)
async def get_bollinger(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> BollingerResponse:
    """Return Bollinger Band data for the given ticker."""
    data = compute_bollinger(ticker.upper())
    return _to_response(data)
