"""Force Index API — Phase F.51.

GET /api/force-index?ticker=<TICKER>
  → Always 200; data_available=False on yfinance failure.
  → 422 if ticker param is missing.
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from quantpilot_stock.force_index.engine import (
    ForceIndexData,
    ForceIndexSignal,
    compute_force_index,
)

router = APIRouter(tags=["force_index"])


class ForceIndexResponse(BaseModel):
    ticker: str
    force_index: float | None
    fi_positive: bool
    fi_direction: str
    fi_normalized: float | None
    fi_score: float
    signal: ForceIndexSignal
    interpretation: str
    as_of_date: str
    data_available: bool


def _to_response(data: ForceIndexData) -> ForceIndexResponse:
    return ForceIndexResponse(
        ticker=data.ticker,
        force_index=data.force_index,
        fi_positive=data.fi_positive,
        fi_direction=data.fi_direction,
        fi_normalized=data.fi_normalized,
        fi_score=data.fi_score,
        signal=data.signal,
        interpretation=data.interpretation,
        as_of_date=data.as_of_date,
        data_available=data.data_available,
    )


@router.get("/force-index", response_model=ForceIndexResponse)
async def get_force_index(
    ticker: str = Query(..., description="Stock ticker symbol (e.g. AAPL)"),
) -> ForceIndexResponse:
    """Return Elder's Force Index data for the given ticker."""
    data = compute_force_index(ticker.upper())
    return _to_response(data)
