"""Mass Index API — Phase F.67.

GET /api/mass_index?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.mass_index.engine import (
    MassIndexData,
    MassIndexSignal,
    compute_mass_index,
)

router = APIRouter(tags=["mass_index"])


class MassIndexResponse(BaseModel):
    ticker: str
    mass_index: float | None
    in_bulge: bool | None
    trending_down: bool | None
    reversal_signal: bool | None
    mi_score: float
    signal: MassIndexSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: MassIndexData) -> MassIndexResponse:
    return MassIndexResponse(
        ticker=data.ticker,
        mass_index=data.mass_index,
        in_bulge=data.in_bulge,
        trending_down=data.trending_down,
        reversal_signal=data.reversal_signal,
        mi_score=data.mi_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/mass_index", response_model=MassIndexResponse)
async def get_mass_index(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> MassIndexResponse:
    """Return Mass Index data for the given ticker."""
    data = compute_mass_index(ticker.upper())
    return _to_response(data)
