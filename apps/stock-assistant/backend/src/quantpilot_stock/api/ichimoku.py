"""Ichimoku Cloud API — Phase F.59.

GET /api/ichimoku?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.ichimoku.engine import (
    IchimokuData,
    IchimokuSignal,
    compute_ichimoku,
)

router = APIRouter(tags=["ichimoku"])


class IchimokuResponse(BaseModel):
    ticker: str
    tenkan: float | None
    kijun: float | None
    senkou_a: float | None
    senkou_b: float | None
    chikou_above: bool | None
    price_vs_cloud: str
    cloud_bullish: bool | None
    tk_bullish: bool | None
    ichimoku_score: float
    signal: IchimokuSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: IchimokuData) -> IchimokuResponse:
    return IchimokuResponse(
        ticker=data.ticker,
        tenkan=data.tenkan,
        kijun=data.kijun,
        senkou_a=data.senkou_a,
        senkou_b=data.senkou_b,
        chikou_above=data.chikou_above,
        price_vs_cloud=data.price_vs_cloud,
        cloud_bullish=data.cloud_bullish,
        tk_bullish=data.tk_bullish,
        ichimoku_score=data.ichimoku_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/ichimoku", response_model=IchimokuResponse)
async def get_ichimoku(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> IchimokuResponse:
    """Return Ichimoku Cloud data for the given ticker."""
    data = compute_ichimoku(ticker.upper())
    return _to_response(data)
