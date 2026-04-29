"""MACD Signal API — Phase F.37.

GET /api/macd?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.macd.engine import (
    MACDData,
    MACDSignal,
    compute_macd,
)

router = APIRouter(tags=["macd"])


class MACDResponse(BaseModel):
    ticker: str
    macd: float | None
    signal_line: float | None
    histogram: float | None
    prev_histogram: float | None
    histogram_expanding: bool
    recent_crossover: bool
    crossover_direction: str
    macd_score: float
    signal: MACDSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: MACDData) -> MACDResponse:
    return MACDResponse(
        ticker=data.ticker,
        macd=data.macd,
        signal_line=data.signal_line,
        histogram=data.histogram,
        prev_histogram=data.prev_histogram,
        histogram_expanding=data.histogram_expanding,
        recent_crossover=data.recent_crossover,
        crossover_direction=data.crossover_direction,
        macd_score=data.macd_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/macd", response_model=MACDResponse)
async def get_macd(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> MACDResponse:
    """Return MACD signal data for the given ticker."""
    data = compute_macd(ticker.upper())
    return _to_response(data)
