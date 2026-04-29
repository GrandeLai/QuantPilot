"""Quant signals API — Beneish M-Score + Russell rebalancing preview endpoints."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from quantpilot_stock.quant_signals.engine import (
    BeneishMScore,
    RussellMembership,
    compute_beneish_mscore,
    estimate_russell_membership,
)

router = APIRouter(prefix="/quant-signals", tags=["quant-signals"])

_executor = ThreadPoolExecutor(max_workers=4)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class BeneishMScoreResponse(BaseModel):
    ticker: str
    m_score: float
    risk_level: str  # "safe" | "grey" | "manipulator"
    ratios: dict[str, float]
    interpretation: str
    as_of_date: date


class RussellMembershipResponse(BaseModel):
    ticker: str
    market_cap_usd: float
    estimated_rank: int | None
    current_index: str
    proximity_score: float
    rebalance_signal: str


class QuantSignalsSummaryResponse(BaseModel):
    ticker: str
    beneish: BeneishMScoreResponse | None
    russell: RussellMembershipResponse | None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _beneish_to_response(b: BeneishMScore) -> BeneishMScoreResponse:
    return BeneishMScoreResponse(
        ticker=b.ticker,
        m_score=b.m_score,
        risk_level=b.risk_level,
        ratios=b.ratios,
        interpretation=b.interpretation,
        as_of_date=b.as_of_date,
    )


def _russell_to_response(r: RussellMembership) -> RussellMembershipResponse:
    return RussellMembershipResponse(
        ticker=r.ticker,
        market_cap_usd=r.market_cap_usd,
        estimated_rank=r.estimated_rank,
        current_index=r.current_index,
        proximity_score=r.proximity_score,
        rebalance_signal=r.rebalance_signal,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/beneish", response_model=BeneishMScoreResponse)
async def get_beneish_mscore(
    ticker: str = Query(..., description="Stock ticker symbol, e.g. AAPL"),
) -> Any:
    """Compute Beneish M-Score earnings manipulation signal for a ticker."""
    ticker = ticker.strip().upper()
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(_executor, compute_beneish_mscore, ticker)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to compute Beneish M-Score for {ticker}. "
                   "Insufficient financial data (requires ≥2 years of statements).",
        )
    return _beneish_to_response(result)


@router.get("/russell", response_model=RussellMembershipResponse)
async def get_russell_membership(
    ticker: str = Query(..., description="Stock ticker symbol, e.g. AAPL"),
) -> Any:
    """Estimate Russell index membership and annual rebalancing signal."""
    ticker = ticker.strip().upper()
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(_executor, estimate_russell_membership, ticker)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unable to estimate Russell membership for {ticker}. "
                   "No market cap data available.",
        )
    return _russell_to_response(result)


@router.get("/summary", response_model=QuantSignalsSummaryResponse)
async def get_quant_signals_summary(
    ticker: str = Query(..., description="Stock ticker symbol, e.g. AAPL"),
) -> Any:
    """Return both Beneish M-Score and Russell membership for a ticker.

    Either component may be None if data is unavailable; the endpoint
    never raises 404 for summary requests.
    """
    ticker = ticker.strip().upper()
    loop = asyncio.get_event_loop()

    beneish_fut = loop.run_in_executor(_executor, compute_beneish_mscore, ticker)
    russell_fut = loop.run_in_executor(_executor, estimate_russell_membership, ticker)

    beneish_result, russell_result = await asyncio.gather(
        beneish_fut, russell_fut, return_exceptions=True
    )

    beneish_resp: BeneishMScoreResponse | None = None
    russell_resp: RussellMembershipResponse | None = None

    if isinstance(beneish_result, BeneishMScore):
        beneish_resp = _beneish_to_response(beneish_result)

    if isinstance(russell_result, RussellMembership):
        russell_resp = _russell_to_response(russell_result)

    return QuantSignalsSummaryResponse(
        ticker=ticker,
        beneish=beneish_resp,
        russell=russell_resp,
    )
