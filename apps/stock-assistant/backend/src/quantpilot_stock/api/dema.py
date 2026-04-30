"""DEMA API — Phase F.75.

GET /api/dema?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.dema.engine import (
    DEMAData,
    DEMASignal,
    compute_dema,
)

router = APIRouter(tags=["dema"])


class DEMAResponse(BaseModel):
    ticker: str
    dema_value: float | None
    price_above_dema: bool | None
    dema_slope_positive: bool | None
    dema_score: float
    signal: DEMASignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: DEMAData) -> DEMAResponse:
    return DEMAResponse(
        ticker=data.ticker,
        dema_value=data.dema_value,
        price_above_dema=data.price_above_dema,
        dema_slope_positive=data.dema_slope_positive,
        dema_score=data.dema_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/dema", response_model=DEMAResponse)
async def get_dema(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> DEMAResponse:
    """Return DEMA signal data for the given ticker."""
    data = compute_dema(ticker.upper())
    return _to_response(data)
