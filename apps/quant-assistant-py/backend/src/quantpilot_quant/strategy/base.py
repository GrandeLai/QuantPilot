"""策略抽象基类 + 数据契约（re-export from common.contracts.strategy）.

所有量化策略必须继承 BaseStrategy 并实现 on_bar 方法。
全部类型现在都集中定义在 quantpilot_common.contracts；本模块仅 re-export
以保持现有代码 ``from quantpilot_quant.strategy.base import ...`` 写法不破坏。
"""

from __future__ import annotations

from quantpilot_common.contracts.order import Order, OrderSide, OrderType
from quantpilot_common.contracts.position import Position
from quantpilot_common.contracts.strategy import BaseStrategy, StrategyContext

__all__ = [
    "BaseStrategy",
    "Order",
    "OrderSide",
    "OrderType",
    "Position",
    "StrategyContext",
]
