"""PEAD module — Post-Earnings Announcement Drift signal."""

from quantpilot_stock.pead.engine import (
    EarningsEvent,
    EarningsSurpriseGrade,
    PEADSignal,
    compute_pead_signal,
)

__all__ = [
    "EarningsEvent",
    "EarningsSurpriseGrade",
    "PEADSignal",
    "compute_pead_signal",
]
