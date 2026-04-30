"""KVO API — Phase F.68.

GET /api/kvo?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.kvo.engine import (
    KVOData,
    KVOSignal,
    compute_kvo,
)

router = APIRouter(tags=["kvo"])


class KVOResponse(BaseModel):
    ticker: str
    kvo_value: float | None
    signal_value: float | None
    kvo_above_signal: bool | None
    kvo_positive: bool | None
    kvo_score: float
    signal: KVOSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: KVOData) -> KVOResponse:
    return KVOResponse(
        ticker=data.ticker,
        kvo_value=data.kvo_value,
        signal_value=data.signal_value,
        kvo_above_signal=data.kvo_above_signal,
        kvo_positive=data.kvo_positive,
        kvo_score=data.kvo_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/kvo", response_model=KVOResponse)
async def get_kvo(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> KVOResponse:
    """Return Klinger Volume Oscillator data for the given ticker."""
    data = compute_kvo(ticker.upper())
    return _to_response(data)
