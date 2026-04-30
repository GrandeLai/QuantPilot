"""CKS API — Phase F.72.

GET /api/cks?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.cks.engine import (
    CKSData,
    CKSSignal,
    compute_cks,
)

router = APIRouter(tags=["cks"])


class CKSResponse(BaseModel):
    ticker: str
    stop_short: float | None
    stop_long: float | None
    close_value: float | None
    price_above_stop: bool | None
    stop_rising: bool | None
    cks_score: float
    signal: CKSSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: CKSData) -> CKSResponse:
    return CKSResponse(
        ticker=data.ticker,
        stop_short=data.stop_short,
        stop_long=data.stop_long,
        close_value=data.close_value,
        price_above_stop=data.price_above_stop,
        stop_rising=data.stop_rising,
        cks_score=data.cks_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/cks", response_model=CKSResponse)
async def get_cks(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> CKSResponse:
    """Return Chande Kroll Stop data for the given ticker."""
    data = compute_cks(ticker.upper())
    return _to_response(data)
