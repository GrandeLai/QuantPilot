"""ROC API — Phase F.47.

GET /api/roc?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.roc.engine import (
    ROCData,
    ROCSignal,
    compute_roc,
)

router = APIRouter(tags=["roc"])


class ROCResponse(BaseModel):
    ticker: str
    roc: float | None
    prev_roc: float | None
    roc_direction: str
    roc_positive: bool
    roc_score: float
    signal: ROCSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: ROCData) -> ROCResponse:
    return ROCResponse(
        ticker=data.ticker,
        roc=data.roc,
        prev_roc=data.prev_roc,
        roc_direction=data.roc_direction,
        roc_positive=data.roc_positive,
        roc_score=data.roc_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/roc", response_model=ROCResponse)
async def get_roc(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> ROCResponse:
    """Return Rate of Change data for the given ticker."""
    data = compute_roc(ticker.upper())
    return _to_response(data)
