"""Short-Term Reversal Signal API — Phase F.34.

GET /api/reversal-signal?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.reversal_signal.engine import (
    ReversalData,
    ReversalSignal,
    compute_reversal,
)

router = APIRouter(tags=["reversal-signal"])


# ---------------------------------------------------------------------------
# Response model
# ---------------------------------------------------------------------------

class ReversalDataResponse(BaseModel):
    ticker: str
    ret_1w: float | None
    ret_4w: float | None
    rel_1w: float | None
    rel_4w: float | None
    vol_ratio: float | None
    reversal_score: float
    signal: ReversalSignal
    interpretation: str
    as_of_date: str
    data_available: bool


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

def _to_response(data: ReversalData) -> ReversalDataResponse:
    return ReversalDataResponse(
        ticker=data.ticker,
        ret_1w=data.ret_1w,
        ret_4w=data.ret_4w,
        rel_1w=data.rel_1w,
        rel_4w=data.rel_4w,
        vol_ratio=data.vol_ratio,
        reversal_score=data.reversal_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/reversal-signal", response_model=ReversalDataResponse)
async def get_reversal_signal(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> ReversalDataResponse:
    """Return short-term reversal signal for the given ticker vs SPY."""
    data = compute_reversal(ticker.upper())
    return _to_response(data)
