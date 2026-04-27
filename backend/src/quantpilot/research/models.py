"""加密研究服务输出模型 (re-export from common.contracts.research)."""

from __future__ import annotations

from quantpilot_common.contracts.research import (
    CryptoResearchDatasetSummary,
    CryptoResearchOptimizationSummary,
    CryptoResearchTrainSummary,
    WalkForwardWindowMetric,
)

__all__ = [
    "CryptoResearchDatasetSummary",
    "WalkForwardWindowMetric",
    "CryptoResearchTrainSummary",
    "CryptoResearchOptimizationSummary",
]
