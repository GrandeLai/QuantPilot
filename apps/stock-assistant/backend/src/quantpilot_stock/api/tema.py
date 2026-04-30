"""TEMA API — Phase F.76.

GET /api/tema?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.tema.engine import (
    TEMAData,
    TEMASignal,
    compute_tema,
)

router = APIRouter(tags=["tema"])


class TEMAResponse(BaseModel):
    ticker: str
    tema_value: float | None
    price_above_tema: bool | None
    tema_slope_positive: bool | None
    tema_score: float
    signal: TEMASignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: TEMAData) -> TEMAResponse:
    return TEMAResponse(
        ticker=data.ticker,
        tema_value=data.tema_value,
        price_above_tema=data.price_above_tema,
        tema_slope_positive=data.tema_slope_positive,
        tema_score=data.tema_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/tema", response_model=TEMAResponse)
async def get_tema(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> TEMAResponse:
    """Return TEMA signal data for the given ticker."""
    data = compute_tema(ticker.upper())
    return _to_response(data)
