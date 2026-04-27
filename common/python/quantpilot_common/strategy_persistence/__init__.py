"""Strategy persistence: file storage + git versioning. Generic, no quant logic."""

from quantpilot_common.strategy_persistence.git_manager import GitManager
from quantpilot_common.strategy_persistence.storage import (
    StrategyMeta,
    StrategyRecord,
    StrategyStorage,
)

__all__ = [
    "GitManager",
    "StrategyMeta",
    "StrategyRecord",
    "StrategyStorage",
]
