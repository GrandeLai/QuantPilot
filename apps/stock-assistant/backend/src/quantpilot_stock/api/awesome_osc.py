"""Awesome Oscillator API — Phase F.78.

GET /api/awesome_osc?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.awesome_osc.engine import (
    AOData,
    AOSignal,
    compute_ao,
)

router = APIRouter(tags=["awesome_osc"])


class AOResponse(BaseModel):
    ticker: str
    ao_value: float | None
    ao_positive: bool | None
    ao_rising: bool | None
    ao_score: float
    signal: AOSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: AOData) -> AOResponse:
    return AOResponse(
        ticker=data.ticker,
        ao_value=data.ao_value,
        ao_positive=data.ao_positive,
        ao_rising=data.ao_rising,
        ao_score=data.ao_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/awesome_osc", response_model=AOResponse)
async def get_awesome_osc(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> AOResponse:
    """Return Awesome Oscillator data for the given ticker."""
    data = compute_ao(ticker.upper())
    return _to_response(data)
