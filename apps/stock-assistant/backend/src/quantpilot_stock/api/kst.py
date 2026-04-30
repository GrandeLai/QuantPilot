"""KST API — Phase F.60.

GET /api/kst?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.kst.engine import (
    KSTData,
    KSTSignal,
    compute_kst,
)

router = APIRouter(tags=["kst"])


class KSTResponse(BaseModel):
    ticker: str
    kst_value: float | None
    signal_line: float | None
    kst_positive: bool | None
    kst_above_signal: bool | None
    kst_score: float
    signal: KSTSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: KSTData) -> KSTResponse:
    return KSTResponse(
        ticker=data.ticker,
        kst_value=data.kst_value,
        signal_line=data.signal_line,
        kst_positive=data.kst_positive,
        kst_above_signal=data.kst_above_signal,
        kst_score=data.kst_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/kst", response_model=KSTResponse)
async def get_kst(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> KSTResponse:
    """Return KST (Know Sure Thing) data for the given ticker."""
    data = compute_kst(ticker.upper())
    return _to_response(data)
