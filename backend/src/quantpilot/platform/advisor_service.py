"""Read models for the investment assistant product."""

from __future__ import annotations

from datetime import UTC, datetime

from quantpilot.api.data import get_storage
from quantpilot.platform.agent_models import AdviceCard, AdviceEvidence
from quantpilot.research.service import CryptoResearchRequest, CryptoResearchService
from quantpilot.research.validation import TimeSeriesValidationConfig


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


def build_crypto_opportunity_cards(symbol: str = "BTC-USDT") -> list[AdviceCard]:
    """Build crypto opportunity cards from the research stack."""
    storage = get_storage()
    summary = CryptoResearchService(storage).train_and_validate(
        CryptoResearchRequest(
            symbol=symbol,
            base_timeframe="15m",
            higher_timeframes=["1h", "4h", "1d", "1w"],
            limit=180,
            validation=TimeSeriesValidationConfig(
                train_size=60,
                test_size=20,
                step_size=20,
                embargo_size=2,
            ),
        )
    )
    now = datetime.now(UTC)
    direction = summary.latest_class_signal
    recommendation = "watch"
    if direction > 0:
        recommendation = "lean_long"
    elif direction < 0:
        recommendation = "avoid_chasing"

    return [
        AdviceCard(
            type="opportunity",
            subject=symbol,
            recommendation=recommendation,
            confidence=max(summary.latest_class_probabilities.values()),
            evidence=[
                AdviceEvidence(
                    source="crypto_research",
                    summary=f"walk-forward {summary.validation_windows} 窗口，均值准确率 {summary.mean_accuracy:.2%}",
                    observed_at=now,
                )
            ],
            risk_notes=[f"反转概率 {summary.reversal_probability:.2%}，注意趋势切换风险"],
            generated_at=now,
            freshness="fresh",
        )
    ]


def build_crypto_risk_cards(symbol: str = "BTC-USDT") -> list[AdviceCard]:
    """Build crypto risk alert cards from the research stack."""
    storage = get_storage()
    summary = CryptoResearchService(storage).train_and_validate(
        CryptoResearchRequest(
            symbol=symbol,
            base_timeframe="15m",
            higher_timeframes=["1h", "4h", "1d", "1w"],
            limit=180,
            validation=TimeSeriesValidationConfig(
                train_size=60,
                test_size=20,
                step_size=20,
                embargo_size=2,
            ),
        )
    )
    now = datetime.now(UTC)
    return [
        AdviceCard(
            type="risk_alert",
            subject=symbol,
            recommendation="reduce_risk" if summary.reversal_probability >= 0.5 else "monitor",
            confidence=summary.reversal_probability,
            evidence=[
                AdviceEvidence(
                    source="reversal_model",
                    summary=f"反转信号 {summary.reversal_signal}，关键特征 {', '.join(summary.reversal_evidence)}",
                    observed_at=now,
                )
            ],
            risk_notes=[f"最新类别概率 {summary.latest_class_probabilities}"],
            generated_at=now,
            freshness="fresh",
        )
    ]
