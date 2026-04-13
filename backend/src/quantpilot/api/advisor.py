"""Investment assistant API endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from quantpilot.platform.advisor_service import (
    build_opportunity_cards,
    build_overview_snapshot,
)

router = APIRouter(prefix="/advisor", tags=["advisor"])


@router.get("/overview")
async def get_advisor_overview() -> dict[str, object]:
    """Return an assistant-ready portfolio overview."""
    return build_overview_snapshot()


@router.get("/opportunities")
async def get_advisor_opportunities() -> dict[str, list[dict[str, object]]]:
    """Return assistant opportunity cards."""
    return {"items": [card.model_dump(mode="json") for card in build_opportunity_cards()]}
