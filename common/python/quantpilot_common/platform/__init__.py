"""Shared platform contracts re-exported from submodules."""

from quantpilot_common.platform.models import (
    DomainHealth,
    DomainStatus,
    FactEnvelope,
    FreshnessState,
    PlatformSummaryResponse,
)
from quantpilot_common.platform.services import build_platform_summary

__all__ = [
    "DomainHealth",
    "DomainStatus",
    "FactEnvelope",
    "FreshnessState",
    "PlatformSummaryResponse",
    "build_platform_summary",
]
