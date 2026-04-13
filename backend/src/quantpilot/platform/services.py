"""Read-only platform service facade."""

from __future__ import annotations

from datetime import UTC, datetime

from quantpilot.platform.models import DomainStatus, FactEnvelope


def build_platform_summary() -> FactEnvelope:
    """Return a shared-platform domain health snapshot."""
    now = datetime.now(UTC)
    domains = {
        "market_data": DomainStatus(
            name="market_data",
            status="ok",
            freshness="fresh",
            updated_at=now,
        ).model_dump(),
        "portfolio_account": DomainStatus(
            name="portfolio_account",
            status="ok",
            freshness="fresh",
            updated_at=now,
        ).model_dump(),
        "strategy_validation": DomainStatus(
            name="strategy_validation",
            status="ok",
            freshness="fresh",
            updated_at=now,
        ).model_dump(),
        "risk": DomainStatus(
            name="risk",
            status="ok",
            freshness="fresh",
            updated_at=now,
        ).model_dump(),
        "execution": DomainStatus(
            name="execution",
            status="ok",
            freshness="fresh",
            updated_at=now,
        ).model_dump(),
        "agent": DomainStatus(
            name="agent",
            status="ok",
            freshness="fresh",
            updated_at=now,
        ).model_dump(),
    }
    return FactEnvelope(
        version=now.date().isoformat(),
        generated_at=now,
        payload={"domains": domains},
    )
