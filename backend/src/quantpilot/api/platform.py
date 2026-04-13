"""Shared platform API endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from quantpilot.platform.services import build_platform_summary

router = APIRouter(prefix="/platform", tags=["platform"])


@router.get("/summary")
async def get_platform_summary() -> dict:
    """Return read-only shared platform status."""
    envelope = build_platform_summary()
    return {
        "version": envelope.version,
        "generated_at": envelope.generated_at,
        "domains": envelope.payload["domains"],
    }
