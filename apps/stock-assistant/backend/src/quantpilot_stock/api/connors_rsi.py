"""Connors RSI API — Phase F.81.

GET /api/connors_rsi?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.connors_rsi.engine import (
    CRSIData,
    CRSISignal,
    compute_crsi,
)

router = APIRouter(tags=["connors_rsi"])


class CRSIResponse(BaseModel):
    ticker: str
    crsi_value: float | None
    rsi3: float | None
    streak_rsi: float | None
    percent_rank: float | None
    crsi_score: float
    signal: CRSISignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: CRSIData) -> CRSIResponse:
    return CRSIResponse(
        ticker=data.ticker,
        crsi_value=data.crsi_value,
        rsi3=data.rsi3,
        streak_rsi=data.streak_rsi,
        percent_rank=data.percent_rank,
        crsi_score=data.crsi_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/connors_rsi", response_model=CRSIResponse)
async def get_connors_rsi(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> CRSIResponse:
    """Return Connors RSI data for the given ticker."""
    data = compute_crsi(ticker.upper())
    return _to_response(data)
