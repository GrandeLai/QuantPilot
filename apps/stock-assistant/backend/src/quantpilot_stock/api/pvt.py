"""PVT API — Phase F.64.

GET /api/pvt?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.pvt.engine import (
    PVTData,
    PVTSignal,
    compute_pvt,
)

router = APIRouter(tags=["pvt"])


class PVTResponse(BaseModel):
    ticker: str
    pvt_above_signal: bool | None
    pvt_slope_positive: bool | None
    pvt_score: float
    signal: PVTSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: PVTData) -> PVTResponse:
    return PVTResponse(
        ticker=data.ticker,
        pvt_above_signal=data.pvt_above_signal,
        pvt_slope_positive=data.pvt_slope_positive,
        pvt_score=data.pvt_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/pvt", response_model=PVTResponse)
async def get_pvt(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> PVTResponse:
    """Return Price Volume Trend data for the given ticker."""
    data = compute_pvt(ticker.upper())
    return _to_response(data)
