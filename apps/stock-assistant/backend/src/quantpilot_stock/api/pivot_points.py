"""Pivot Points API — F.85.

GET /api/pivot_points?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.pivot_points.engine import (
    PivotData,
    PivotSignal,
    compute_pivot_points,
)

router = APIRouter(tags=["pivot_points"])


class PivotResponse(BaseModel):
    """HTTP response model for Pivot Points support/resistance analysis."""

    ticker: str
    pp: float | None
    r1: float | None
    r2: float | None
    r3: float | None
    s1: float | None
    s2: float | None
    s3: float | None
    close: float | None
    pivot_score: float
    signal: PivotSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: PivotData) -> PivotResponse:
    return PivotResponse(
        ticker=data.ticker,
        pp=data.pp,
        r1=data.r1,
        r2=data.r2,
        r3=data.r3,
        s1=data.s1,
        s2=data.s2,
        s3=data.s3,
        close=data.close,
        pivot_score=data.pivot_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/pivot_points", response_model=PivotResponse)
async def get_pivot_points(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> PivotResponse:
    """Return Pivot Points data for the given ticker."""
    data = compute_pivot_points(ticker.upper())
    return _to_response(data)
