"""Fisher Transform API — F.82.

GET /api/fisher_transform?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.fisher_transform.engine import (
    FisherData,
    FisherSignal,
    compute_fisher,
)

router = APIRouter(tags=["fisher_transform"])


class FisherResponse(BaseModel):
    ticker: str
    fisher_value: float | None
    fisher_signal: float | None
    fisher_score: float
    signal: FisherSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: FisherData) -> FisherResponse:
    return FisherResponse(
        ticker=data.ticker,
        fisher_value=data.fisher_value,
        fisher_signal=data.fisher_signal,
        fisher_score=data.fisher_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/fisher_transform", response_model=FisherResponse)
async def get_fisher_transform(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> FisherResponse:
    """Return Fisher Transform data for the given ticker."""
    data = compute_fisher(ticker.upper())
    return _to_response(data)
