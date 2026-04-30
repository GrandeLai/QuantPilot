"""MFI API — Phase F.42.

GET /api/mfi?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.mfi.engine import (
    MFIData,
    MFISignal,
    compute_mfi,
)

router = APIRouter(tags=["mfi"])


class MFIResponse(BaseModel):
    ticker: str
    mfi: float | None
    prev_mfi: float | None
    mfi_direction: str
    overbought: bool
    oversold: bool
    bullish_divergence: bool
    bearish_divergence: bool
    mfi_score: float
    signal: MFISignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: MFIData) -> MFIResponse:
    return MFIResponse(
        ticker=data.ticker,
        mfi=data.mfi,
        prev_mfi=data.prev_mfi,
        mfi_direction=data.mfi_direction,
        overbought=data.overbought,
        oversold=data.oversold,
        bullish_divergence=data.bullish_divergence,
        bearish_divergence=data.bearish_divergence,
        mfi_score=data.mfi_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/mfi", response_model=MFIResponse)
async def get_mfi(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> MFIResponse:
    """Return Money Flow Index data for the given ticker."""
    data = compute_mfi(ticker.upper())
    return _to_response(data)
