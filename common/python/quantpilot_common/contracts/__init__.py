"""Pure data contracts shared across QuantPilot products.

These contracts are intentionally behavior-light (dataclasses + light helpers)
so both stock-assistant and quant-assistant(-py) can depend on them without
implying coupling to either side's business logic.
"""

from quantpilot_common.contracts.agent_advice import AdviceCard, AdviceEvidence, AdviceType
from quantpilot_common.contracts.order import Order, OrderSide, OrderType
from quantpilot_common.contracts.position import Position
from quantpilot_common.contracts.risk import RiskCheckResult, RiskConfig
from quantpilot_common.contracts.strategy import BaseStrategy, StrategyContext
from quantpilot_common.contracts.trade import TradeRecord
from quantpilot_common.contracts.validation import TimeSeriesValidationConfig, ValidationWindow

__all__ = [
    "AdviceCard",
    "AdviceEvidence",
    "AdviceType",
    "BaseStrategy",
    "Order",
    "OrderSide",
    "OrderType",
    "Position",
    "RiskCheckResult",
    "RiskConfig",
    "StrategyContext",
    "TimeSeriesValidationConfig",
    "TradeRecord",
    "ValidationWindow",
]
