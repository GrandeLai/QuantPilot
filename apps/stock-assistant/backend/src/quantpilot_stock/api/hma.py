"""HMA API — Phase F.69.

GET /api/hma?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.hma.engine import (
    HMAData,
    HMASignal,
    compute_hma,
)

router = APIRouter(tags=["hma"])


class HMAResponse(BaseModel):
    ticker: str
    hma_value: float | None
    close_value: float | None
    price_above_hma: bool | None
    hma_rising: bool | None
    hma_score: float
    signal: HMASignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: HMAData) -> HMAResponse:
    return HMAResponse(
        ticker=data.ticker,
        hma_value=data.hma_value,
        close_value=data.close_value,
        price_above_hma=data.price_above_hma,
        hma_rising=data.hma_rising,
        hma_score=data.hma_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/hma", response_model=HMAResponse)
async def get_hma(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> HMAResponse:
    """Return Hull Moving Average data for the given ticker."""
    data = compute_hma(ticker.upper())
    return _to_response(data)
