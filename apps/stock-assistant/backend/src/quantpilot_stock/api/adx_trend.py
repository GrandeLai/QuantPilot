"""ADX Trend Strength API — Phase F.35.

GET /api/adx-trend?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.adx_trend.engine import (
    ADXData,
    TrendSignal,
    TrendStrength,
    compute_adx_trend,
)

router = APIRouter(tags=["adx-trend"])


class ADXDataResponse(BaseModel):
    ticker: str
    adx: float | None
    plus_di: float | None
    minus_di: float | None
    atr: float | None
    signal: TrendSignal
    trend_strength: TrendStrength
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: ADXData) -> ADXDataResponse:
    return ADXDataResponse(
        ticker=data.ticker,
        adx=data.adx,
        plus_di=data.plus_di,
        minus_di=data.minus_di,
        atr=data.atr,
        signal=data.signal,
        trend_strength=data.trend_strength,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/adx-trend", response_model=ADXDataResponse)
async def get_adx_trend(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> ADXDataResponse:
    """Return ADX trend strength indicator for the given ticker."""
    data = compute_adx_trend(ticker.upper())
    return _to_response(data)
