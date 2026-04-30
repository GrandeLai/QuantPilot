"""OBV API — Phase F.41.

GET /api/obv?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.obv.engine import (
    OBVData,
    OBVSignal,
    compute_obv,
)

router = APIRouter(tags=["obv"])


class OBVResponse(BaseModel):
    ticker: str
    obv: float | None
    obv_ema20: float | None
    obv_above_ema: bool
    obv_5d_change_pct: float | None
    price_5d_change_pct: float | None
    price_obv_trend: str
    obv_score: float
    signal: OBVSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: OBVData) -> OBVResponse:
    return OBVResponse(
        ticker=data.ticker,
        obv=data.obv,
        obv_ema20=data.obv_ema20,
        obv_above_ema=data.obv_above_ema,
        obv_5d_change_pct=data.obv_5d_change_pct,
        price_5d_change_pct=data.price_5d_change_pct,
        price_obv_trend=data.price_obv_trend,
        obv_score=data.obv_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/obv", response_model=OBVResponse)
async def get_obv(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> OBVResponse:
    """Return On-Balance Volume data for the given ticker."""
    data = compute_obv(ticker.upper())
    return _to_response(data)
