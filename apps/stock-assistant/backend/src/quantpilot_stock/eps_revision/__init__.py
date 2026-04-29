"""EPS Revision Momentum module — analyst estimate revision tracker."""

from quantpilot_stock.eps_revision.engine import (
    AnalystTargets,
    EpsRevisionMomentum,
    EpsRevisionPeriod,
    compute_eps_revision_momentum,
)

__all__ = [
    "AnalystTargets",
    "EpsRevisionMomentum",
    "EpsRevisionPeriod",
    "compute_eps_revision_momentum",
]
