"""Price Oscillator (PO) API — Phase F.73.

GET /api/price_osc?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.price_osc.engine import (
    POData,
    POSignal,
    compute_po,
)

router = APIRouter(tags=["price_osc"])


class POResponse(BaseModel):
    ticker: str
    po_value: float | None
    signal_value: float | None
    po_above_signal: bool | None
    po_positive: bool | None
    po_score: float
    signal: POSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: POData) -> POResponse:
    return POResponse(
        ticker=data.ticker,
        po_value=data.po_value,
        signal_value=data.signal_value,
        po_above_signal=data.po_above_signal,
        po_positive=data.po_positive,
        po_score=data.po_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/price_osc", response_model=POResponse)
async def get_price_osc(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> POResponse:
    """Return Price Oscillator data for the given ticker."""
    data = compute_po(ticker.upper())
    return _to_response(data)
