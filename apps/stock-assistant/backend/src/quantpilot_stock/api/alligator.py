"""Williams Alligator API — Phase F.77.

GET /api/alligator?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.alligator.engine import (
    AlligatorData,
    AlligatorSignal,
    compute_alligator,
)

router = APIRouter(tags=["alligator"])


class AlligatorResponse(BaseModel):
    ticker: str
    jaw: float | None
    teeth: float | None
    lips: float | None
    lips_above_teeth: bool | None
    teeth_above_jaw: bool | None
    price_above_jaw: bool | None
    alligator_score: float
    signal: AlligatorSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: AlligatorData) -> AlligatorResponse:
    return AlligatorResponse(
        ticker=data.ticker,
        jaw=data.jaw,
        teeth=data.teeth,
        lips=data.lips,
        lips_above_teeth=data.lips_above_teeth,
        teeth_above_jaw=data.teeth_above_jaw,
        price_above_jaw=data.price_above_jaw,
        alligator_score=data.alligator_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/alligator", response_model=AlligatorResponse)
async def get_alligator(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> AlligatorResponse:
    """Return Williams Alligator data for the given ticker."""
    data = compute_alligator(ticker.upper())
    return _to_response(data)
