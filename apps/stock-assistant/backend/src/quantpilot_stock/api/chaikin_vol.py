"""Chaikin Volatility API — Phase F.74.

GET /api/chaikin_vol?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.chaikin_vol.engine import (
    CVData,
    CVSignal,
    compute_cv,
)

router = APIRouter(tags=["chaikin_vol"])


class CVResponse(BaseModel):
    ticker: str
    cv_value: float | None
    vol_expanding: bool | None
    price_above_sma: bool | None
    cv_score: float
    signal: CVSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: CVData) -> CVResponse:
    return CVResponse(
        ticker=data.ticker,
        cv_value=data.cv_value,
        vol_expanding=data.vol_expanding,
        price_above_sma=data.price_above_sma,
        cv_score=data.cv_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/chaikin_vol", response_model=CVResponse)
async def get_chaikin_vol(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> CVResponse:
    """Return Chaikin Volatility data for the given ticker."""
    data = compute_cv(ticker.upper())
    return _to_response(data)
