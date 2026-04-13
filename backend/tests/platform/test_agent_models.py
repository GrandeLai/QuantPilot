"""Tests for structured assistant advice contracts."""

from datetime import UTC, datetime

from quantpilot.platform.agent_models import AdviceCard, AdviceEvidence


def test_advice_card_requires_evidence_and_risk_notes() -> None:
    card = AdviceCard(
        type="opportunity",
        subject="AAPL",
        recommendation="watch",
        confidence=0.72,
        evidence=[
            AdviceEvidence(
                source="screener",
                summary="relative strength improving",
                observed_at=datetime(2026, 4, 13, tzinfo=UTC),
            )
        ],
        risk_notes=["earnings this week"],
        generated_at=datetime(2026, 4, 13, tzinfo=UTC),
        freshness="fresh",
    )

    assert card.type == "opportunity"
    assert card.evidence[0].source == "screener"
    assert card.risk_notes == ["earnings this week"]
