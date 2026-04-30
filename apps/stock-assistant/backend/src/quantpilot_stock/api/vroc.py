"""Volume Rate of Change API — F.84.

GET /api/vroc?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.vroc.engine import (
    VROCData,
    VROCSignal,
    compute_vroc,
)

router = APIRouter(tags=["vroc"])


class VROCResponse(BaseModel):
    ticker: str
    vroc_value: float | None
    vroc_score: float
    signal: VROCSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: VROCData) -> VROCResponse:
    return VROCResponse(
        ticker=data.ticker,
        vroc_value=data.vroc_value,
        vroc_score=data.vroc_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/vroc", response_model=VROCResponse)
async def get_vroc(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> VROCResponse:
    """Return Volume Rate of Change data for the given ticker."""
    data = compute_vroc(ticker.upper())
    return _to_response(data)
