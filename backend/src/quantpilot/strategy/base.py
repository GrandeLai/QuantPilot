"""策略抽象基类 — BaseStrategy.

所有量化策略必须继承此类，并实现 on_bar 方法。
事件驱动架构：on_init → on_bar* → on_stop
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quantpilot_common.data.models import OHLCVBar


class OrderSide(StrEnum):
    """订单方向."""

    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    """订单类型."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


@dataclass
class Order:
    """订单对象."""

    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: float | None = None    # 限价单价格
    stop_price: float | None = None  # 止损触发价
    strategy_id: str = ""
    comment: str = ""


@dataclass
class Position:
    """持仓对象."""

    symbol: str
    quantity: float          # 正数多头，负数空头
    avg_price: float
    unrealized_pnl: float = 0.0

    @property
    def is_long(self) -> bool:
        return self.quantity > 0

    @property
    def is_short(self) -> bool:
        return self.quantity < 0


@dataclass
class StrategyContext:
    """策略运行时上下文，由回测引擎注入."""

    symbol: str
    timeframe: str
    initial_cash: float = 1_000_000.0
    cash: float = 0.0
    positions: dict[str, Position] = field(default_factory=dict)
    orders: list[Order] = field(default_factory=list)
    params: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.cash == 0.0:
            self.cash = self.initial_cash

    def buy(
        self,
        symbol: str,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        price: float | None = None,
        comment: str = "",
    ) -> Order:
        """创建买入订单."""
        order = Order(
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=order_type,
            quantity=quantity,
            price=price,
            comment=comment,
        )
        self.orders.append(order)
        return order

    def sell(
        self,
        symbol: str,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        price: float | None = None,
        comment: str = "",
    ) -> Order:
        """创建卖出订单."""
        order = Order(
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=order_type,
            quantity=quantity,
            price=price,
            comment=comment,
        )
        self.orders.append(order)
        return order

    def get_position(self, symbol: str) -> Position | None:
        return self.positions.get(symbol)

    def portfolio_value(self, current_prices: dict[str, float]) -> float:
        """计算组合总价值."""
        equity = sum(
            pos.quantity * current_prices.get(pos.symbol, pos.avg_price)
            for pos in self.positions.values()
        )
        return self.cash + equity


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
