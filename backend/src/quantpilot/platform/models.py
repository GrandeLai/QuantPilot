"""Shared platform contract models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

DomainHealth = Literal["ok", "degraded", "error"]
FreshnessState = Literal["fresh", "stale", "unknown"]


class DomainStatus(BaseModel):
    """Status block for a shared platform domain."""

    name: str
    status: DomainHealth
    freshness: FreshnessState
    updated_at: datetime
    detail: str | None = None


class FactEnvelope(BaseModel):
    """Versioned fact wrapper consumed by multiple products."""

    version: str = Field(min_length=1)
    generated_at: datetime
    payload: dict[str, Any]
