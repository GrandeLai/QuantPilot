"""Stock-assistant-specific platform pieces (advisor + agent models).

Phase A note: shared platform contracts (DomainStatus, FactEnvelope,
PlatformSummaryResponse, build_platform_summary) have been moved to
``quantpilot_common.platform`` (PR 3). Only stock-assistant-specific
pieces remain here pending migration to ``apps/stock-assistant`` in
PR 4.
"""

from quantpilot.platform.agent_models import AdviceCard, AdviceEvidence

__all__ = [
    "AdviceCard",
    "AdviceEvidence",
]
