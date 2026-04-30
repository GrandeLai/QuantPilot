"""Donchian Channels API — Phase F.58.

GET /api/donchian?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.donchian.engine import (
    DonchianData,
    DonchianSignal,
    compute_donchian,
)

router = APIRouter(tags=["donchian"])


class DonchianResponse(BaseModel):
    ticker: str
    upper: float | None
    lower: float | None
    middle: float | None
    position: float | None
    channel_width_pct: float | None
    donchian_score: float
    signal: DonchianSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: DonchianData) -> DonchianResponse:
    return DonchianResponse(
        ticker=data.ticker,
        upper=data.upper,
        lower=data.lower,
        middle=data.middle,
        position=data.position,
        channel_width_pct=data.channel_width_pct,
        donchian_score=data.donchian_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/donchian", response_model=DonchianResponse)
async def get_donchian(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> DonchianResponse:
    """Return Donchian Channels data for the given ticker."""
    data = compute_donchian(ticker.upper())
    return _to_response(data)
