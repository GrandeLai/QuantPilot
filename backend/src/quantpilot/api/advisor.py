"""Investment assistant API endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from quantpilot.platform.advisor_service import (
    build_opportunity_cards,
    build_overview_snapshot,
)
from quantpilot.platform.agent_models import AdviceCard

router = APIRouter(prefix="/advisor", tags=["advisor"])


class AdvisorOverviewResponse(BaseModel):
    """Typed overview response for the investment assistant."""

    net_worth: float
    cash_ratio: float
    positions: list[dict[str, object]]
    generated_at: datetime


class AdvisorOpportunitiesResponse(BaseModel):
    """Typed opportunity-card response for the investment assistant."""

    items: list[AdviceCard]


@router.get("/overview", response_model=AdvisorOverviewResponse)
async def get_advisor_overview() -> AdvisorOverviewResponse:
    """Return an assistant-ready portfolio overview."""
    return AdvisorOverviewResponse.model_validate(build_overview_snapshot())


@router.get("/opportunities", response_model=AdvisorOpportunitiesResponse)
async def get_advisor_opportunities() -> AdvisorOpportunitiesResponse:
    """Return assistant opportunity cards."""
    return AdvisorOpportunitiesResponse(items=build_opportunity_cards())
