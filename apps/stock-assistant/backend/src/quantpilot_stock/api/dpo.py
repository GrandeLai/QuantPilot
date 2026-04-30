"""DPO API — Phase F.56.

GET /api/dpo?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.dpo.engine import (
    DPOData,
    DPOSignal,
    compute_dpo,
)

router = APIRouter(tags=["dpo"])


class DPOResponse(BaseModel):
    ticker: str
    dpo_value: float | None
    dpo_positive: bool
    dpo_score: float
    signal: DPOSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: DPOData) -> DPOResponse:
    return DPOResponse(
        ticker=data.ticker,
        dpo_value=data.dpo_value,
        dpo_positive=data.dpo_positive,
        dpo_score=data.dpo_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/dpo", response_model=DPOResponse)
async def get_dpo(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> DPOResponse:
    """Return DPO (Detrended Price Oscillator) data for the given ticker."""
    data = compute_dpo(ticker.upper())
    return _to_response(data)
