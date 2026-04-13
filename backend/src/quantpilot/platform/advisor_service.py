"""Read models for the investment assistant product."""

from __future__ import annotations

from datetime import UTC, datetime

from quantpilot.platform.agent_models import AdviceCard, AdviceEvidence


def build_overview_snapshot() -> dict[str, object]:
    """Return a lightweight portfolio overview snapshot."""
    now = datetime.now(UTC)
    return {
        "net_worth": 100000.0,
        "cash_ratio": 0.35,
        "positions": [],
        "generated_at": now,
    }


def build_opportunity_cards() -> list[AdviceCard]:
    """Return assistant opportunity cards."""
    now = datetime.now(UTC)
    return [
        AdviceCard(
            type="opportunity",
            subject="AAPL",
            recommendation="watch",
            confidence=0.68,
            evidence=[
                AdviceEvidence(
                    source="market_data",
                    summary="relative strength is improving against recent range",
                    observed_at=now,
                )
            ],
            risk_notes=["earnings event risk remains elevated"],
            generated_at=now,
            freshness="fresh",
        )
    ]
