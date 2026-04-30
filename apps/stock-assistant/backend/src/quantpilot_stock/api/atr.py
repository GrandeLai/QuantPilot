"""ATR API — Phase F.46.

GET /api/atr?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.atr.engine import (
    ATRData,
    ATRSignal,
    compute_atr,
)

router = APIRouter(tags=["atr"])


class ATRResponse(BaseModel):
    ticker: str
    atr: float | None
    atr_pct: float | None
    atr_pct_rank: float | None
    volatility_regime: str
    above_sma20: bool
    above_sma50: bool
    atr_score: float
    signal: ATRSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: ATRData) -> ATRResponse:
    return ATRResponse(
        ticker=data.ticker,
        atr=data.atr,
        atr_pct=data.atr_pct,
        atr_pct_rank=data.atr_pct_rank,
        volatility_regime=data.volatility_regime,
        above_sma20=data.above_sma20,
        above_sma50=data.above_sma50,
        atr_score=data.atr_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/atr", response_model=ATRResponse)
async def get_atr(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> ATRResponse:
    """Return Average True Range data for the given ticker."""
    data = compute_atr(ticker.upper())
    return _to_response(data)
