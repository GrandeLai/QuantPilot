"""Parabolic SAR API — Phase F.48.

GET /api/sar?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.sar.engine import (
    SARData,
    SARSignal,
    compute_sar,
)

router = APIRouter(tags=["sar"])


class SARResponse(BaseModel):
    ticker: str
    sar: float | None
    sar_distance_pct: float | None
    sar_bullish: bool
    sar_direction: str
    trend_bars: int
    sar_score: float
    signal: SARSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: SARData) -> SARResponse:
    return SARResponse(
        ticker=data.ticker,
        sar=data.sar,
        sar_distance_pct=data.sar_distance_pct,
        sar_bullish=data.sar_bullish,
        sar_direction=data.sar_direction,
        trend_bars=data.trend_bars,
        sar_score=data.sar_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/sar", response_model=SARResponse)
async def get_sar(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> SARResponse:
    """Return Parabolic SAR data for the given ticker."""
    data = compute_sar(ticker.upper())
    return _to_response(data)
