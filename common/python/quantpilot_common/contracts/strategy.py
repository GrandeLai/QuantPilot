"""策略上下文数据契约（不含策略基类，BaseStrategy 留在量化模块）."""

from __future__ import annotations

from dataclasses import dataclass, field

from quantpilot_common.contracts.order import Order, OrderSide, OrderType
from quantpilot_common.contracts.position import Position


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
