"""CMF API — Phase F.43.

GET /api/cmf?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.cmf.engine import (
    CMFData,
    CMFSignal,
    compute_cmf,
)

router = APIRouter(tags=["cmf"])


class CMFResponse(BaseModel):
    ticker: str
    cmf: float | None
    prev_cmf: float | None
    cmf_direction: str
    cmf_positive: bool
    cmf_strong_bull: bool
    cmf_strong_bear: bool
    cmf_score: float
    signal: CMFSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: CMFData) -> CMFResponse:
    return CMFResponse(
        ticker=data.ticker,
        cmf=data.cmf,
        prev_cmf=data.prev_cmf,
        cmf_direction=data.cmf_direction,
        cmf_positive=data.cmf_positive,
        cmf_strong_bull=data.cmf_strong_bull,
        cmf_strong_bear=data.cmf_strong_bear,
        cmf_score=data.cmf_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/cmf", response_model=CMFResponse)
async def get_cmf(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> CMFResponse:
    """Return Chaikin Money Flow data for the given ticker."""
    data = compute_cmf(ticker.upper())
    return _to_response(data)
