"""VWAP API — Phase F.49.

GET /api/vwap?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.vwap.engine import (
    VWAPData,
    VWAPSignal,
    compute_vwap,
)

router = APIRouter(tags=["vwap"])


class VWAPResponse(BaseModel):
    ticker: str
    vwap: float | None
    vwap_deviation_pct: float | None
    above_vwap: bool
    vwap_slope: str
    vwap_score: float
    signal: VWAPSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: VWAPData) -> VWAPResponse:
    return VWAPResponse(
        ticker=data.ticker,
        vwap=data.vwap,
        vwap_deviation_pct=data.vwap_deviation_pct,
        above_vwap=data.above_vwap,
        vwap_slope=data.vwap_slope,
        vwap_score=data.vwap_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/vwap", response_model=VWAPResponse)
async def get_vwap(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> VWAPResponse:
    """Return rolling 20-day VWAP data for the given ticker."""
    data = compute_vwap(ticker.upper())
    return _to_response(data)
