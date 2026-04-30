"""KAMA API — Phase F.70.

GET /api/kama?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.kama.engine import (
    KAMAData,
    KAMASignal,
    compute_kama,
)

router = APIRouter(tags=["kama"])


class KAMAResponse(BaseModel):
    ticker: str
    kama_value: float | None
    close_value: float | None
    price_above_kama: bool | None
    kama_rising: bool | None
    kama_score: float
    signal: KAMASignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: KAMAData) -> KAMAResponse:
    return KAMAResponse(
        ticker=data.ticker,
        kama_value=data.kama_value,
        close_value=data.close_value,
        price_above_kama=data.price_above_kama,
        kama_rising=data.kama_rising,
        kama_score=data.kama_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/kama", response_model=KAMAResponse)
async def get_kama(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> KAMAResponse:
    """Return Kaufman Adaptive Moving Average data for the given ticker."""
    data = compute_kama(ticker.upper())
    return _to_response(data)
