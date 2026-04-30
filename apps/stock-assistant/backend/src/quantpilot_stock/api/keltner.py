"""Keltner Channel API — Phase F.50.

GET /api/keltner?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.keltner.engine import (
    KeltnerData,
    KeltnerSignal,
    compute_keltner,
)

router = APIRouter(tags=["keltner"])


class KeltnerResponse(BaseModel):
    ticker: str
    upper: float | None
    middle: float | None
    lower: float | None
    kc_position: float | None
    above_upper: bool
    below_lower: bool
    channel_width_pct: float | None
    kc_score: float
    signal: KeltnerSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: KeltnerData) -> KeltnerResponse:
    return KeltnerResponse(
        ticker=data.ticker,
        upper=data.upper,
        middle=data.middle,
        lower=data.lower,
        kc_position=data.kc_position,
        above_upper=data.above_upper,
        below_lower=data.below_lower,
        channel_width_pct=data.channel_width_pct,
        kc_score=data.kc_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/keltner", response_model=KeltnerResponse)
async def get_keltner(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> KeltnerResponse:
    """Return Keltner Channel data for the given ticker."""
    data = compute_keltner(ticker.upper())
    return _to_response(data)
