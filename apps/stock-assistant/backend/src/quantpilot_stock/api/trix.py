"""TRIX API — Phase F.52.

GET /api/trix?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.trix.engine import (
    TRIXData,
    TRIXSignal,
    compute_trix,
)

router = APIRouter(tags=["trix"])


class TRIXResponse(BaseModel):
    ticker: str
    trix: float | None
    signal_line: float | None
    trix_positive: bool
    trix_above_signal: bool
    trix_score: float
    signal: TRIXSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: TRIXData) -> TRIXResponse:
    return TRIXResponse(
        ticker=data.ticker,
        trix=data.trix,
        signal_line=data.signal_line,
        trix_positive=data.trix_positive,
        trix_above_signal=data.trix_above_signal,
        trix_score=data.trix_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/trix", response_model=TRIXResponse)
async def get_trix(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> TRIXResponse:
    """Return TRIX (triple EMA rate of change) data for the given ticker."""
    data = compute_trix(ticker.upper())
    return _to_response(data)
