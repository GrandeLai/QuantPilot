"""Pure data contracts shared across QuantPilot products.

These contracts are intentionally behavior-light (dataclasses + light helpers)
so both stock-assistant and quant-assistant(-py) can depend on them without
implying coupling to either side's business logic.
"""

from quantpilot_common.contracts.order import Order, OrderSide, OrderType
from quantpilot_common.contracts.position import Position
from quantpilot_common.contracts.strategy import StrategyContext
from quantpilot_common.contracts.risk import RiskConfig, RiskCheckResult
from quantpilot_common.contracts.trade import TradeRecord
from quantpilot_common.contracts.validation import TimeSeriesValidationConfig, ValidationWindow

__all__ = [
    "Order",
    "OrderSide",
    "OrderType",
    "Position",
    "StrategyContext",
    "RiskConfig",
    "RiskCheckResult",
    "TradeRecord",
    "TimeSeriesValidationConfig",
    "ValidationWindow",
]
