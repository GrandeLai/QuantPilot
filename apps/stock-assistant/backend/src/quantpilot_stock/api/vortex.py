"""Vortex Indicator API — Phase F.63.

GET /api/vortex?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.vortex.engine import (
    VortexData,
    VortexSignal,
    compute_vortex,
)

router = APIRouter(tags=["vortex"])


class VortexResponse(BaseModel):
    ticker: str
    vi_plus: float | None
    vi_minus: float | None
    vi_spread: float | None
    vi_bullish: bool | None
    vortex_score: float
    signal: VortexSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: VortexData) -> VortexResponse:
    return VortexResponse(
        ticker=data.ticker,
        vi_plus=data.vi_plus,
        vi_minus=data.vi_minus,
        vi_spread=data.vi_spread,
        vi_bullish=data.vi_bullish,
        vortex_score=data.vortex_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/vortex", response_model=VortexResponse)
async def get_vortex(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> VortexResponse:
    """Return Vortex Indicator data for the given ticker."""
    data = compute_vortex(ticker.upper())
    return _to_response(data)
