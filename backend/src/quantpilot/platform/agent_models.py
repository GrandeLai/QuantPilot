"""Structured advice contracts shared by workbench and assistant."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from quantpilot.platform.models import FreshnessState

AdviceType = Literal[
    "opportunity",
    "rebalance_recommendation",
    "risk_alert",
    "strategy_diagnosis",
    "portfolio_review",
]


class AdviceEvidence(BaseModel):
    """Evidence attached to a structured advice card."""

    source: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    observed_at: datetime


class AdviceCard(BaseModel):
    """Shared AI suggestion payload."""

    type: AdviceType
    subject: str = Field(min_length=1)
    recommendation: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[AdviceEvidence]
    risk_notes: list[str]
    generated_at: datetime
    freshness: FreshnessState
