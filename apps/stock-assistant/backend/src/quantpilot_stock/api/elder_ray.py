"""Elder Ray Index API — Phase F.62.

GET /api/elder_ray?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.elder_ray.engine import (
    ElderRayData,
    ElderRaySignal,
    compute_elder_ray,
)

router = APIRouter(tags=["elder_ray"])


class ElderRayResponse(BaseModel):
    ticker: str
    bull_power: float | None
    bear_power: float | None
    ema13: float | None
    bull_positive: bool | None
    bear_rising: bool | None
    elder_ray_score: float
    signal: ElderRaySignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: ElderRayData) -> ElderRayResponse:
    return ElderRayResponse(
        ticker=data.ticker,
        bull_power=data.bull_power,
        bear_power=data.bear_power,
        ema13=data.ema13,
        bull_positive=data.bull_positive,
        bear_rising=data.bear_rising,
        elder_ray_score=data.elder_ray_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/elder_ray", response_model=ElderRayResponse)
async def get_elder_ray(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> ElderRayResponse:
    """Return Elder Ray Index data for the given ticker."""
    data = compute_elder_ray(ticker.upper())
    return _to_response(data)
