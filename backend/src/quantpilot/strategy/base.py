"""策略抽象基类 — BaseStrategy.

所有量化策略必须继承此类，并实现 on_bar 方法。
事件驱动架构：on_init → on_bar* → on_stop

数据契约（Order/Position/StrategyContext/OrderSide/OrderType）已下沉到
``quantpilot_common.contracts``；本模块从那里 re-export 以保持向后兼容。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from quantpilot_common.contracts.order import Order, OrderSide, OrderType
from quantpilot_common.contracts.position import Position
from quantpilot_common.contracts.strategy import StrategyContext

if TYPE_CHECKING:
    from quantpilot_common.data.models import OHLCVBar


__all__ = [
    "Order",
    "OrderSide",
    "OrderType",
    "Position",
    "StrategyContext",
    "BaseStrategy",
]


class BaseStrategy(ABC):
    """量化策略抽象基类.

    子类必须实现：
        - on_bar(bar, context): 每根 K 线到达时的处理逻辑

    可选覆盖：
        - on_init(context): 策略初始化
        - on_stop(context): 策略停止时的清仓/汇报逻辑
    """

    # 策略元信息（子类覆盖）
    name: str = "BaseStrategy"
    description: str = ""
    version: str = "1.0.0"
    author: str = ""

    # 默认参数（子类覆盖）
    default_params: dict[str, object] = {}

    def on_init(self, context: StrategyContext) -> None:  # noqa: B027
        """策略初始化（可选覆盖）."""

    @abstractmethod
    def on_bar(self, bar: OHLCVBar, context: StrategyContext) -> None:
        """处理新 K 线（子类必须实现）.

        Args:
            bar: 当前 K 线数据
            context: 策略运行时上下文（持仓、资金、下单接口）
        """

    def on_stop(self, context: StrategyContext) -> None:  # noqa: B027
        """策略停止时执行（可选覆盖）."""

    def get_param(self, context: StrategyContext, key: str, default: object = None) -> object:
        """获取策略参数（优先从 context.params 读取，否则使用 default_params）."""
        return context.params.get(key, self.default_params.get(key, default))
