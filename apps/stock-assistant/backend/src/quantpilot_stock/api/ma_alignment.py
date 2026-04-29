"""Moving Average Alignment API — Phase F.36.

GET /api/ma-alignment?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.ma_alignment.engine import (
    MAAlignmentData,
    MASignal,
    compute_ma_alignment,
)

router = APIRouter(tags=["ma-alignment"])


class MAAlignmentResponse(BaseModel):
    ticker: str
    price: float | None
    sma20: float | None
    sma50: float | None
    sma200: float | None
    dist_from_20: float | None
    dist_from_50: float | None
    dist_from_200: float | None
    ma_score: float
    golden_cross: bool
    full_bull_align: bool
    full_bear_align: bool
    signal: MASignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: MAAlignmentData) -> MAAlignmentResponse:
    return MAAlignmentResponse(
        ticker=data.ticker,
        price=data.price,
        sma20=data.sma20,
        sma50=data.sma50,
        sma200=data.sma200,
        dist_from_20=data.dist_from_20,
        dist_from_50=data.dist_from_50,
        dist_from_200=data.dist_from_200,
        ma_score=data.ma_score,
        golden_cross=data.golden_cross,
        full_bull_align=data.full_bull_align,
        full_bear_align=data.full_bear_align,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/ma-alignment", response_model=MAAlignmentResponse)
async def get_ma_alignment(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> MAAlignmentResponse:
    """Return moving average alignment score for the given ticker."""
    data = compute_ma_alignment(ticker.upper())
    return _to_response(data)
