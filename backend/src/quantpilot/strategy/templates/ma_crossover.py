"""策略模板 1：移动均线交叉策略.

信号逻辑：
  - 快线上穿慢线（金叉）→ 买入
  - 快线下穿慢线（死叉）→ 卖出
"""

from collections import deque

from quantpilot.data.models import OHLCVBar
from quantpilot.strategy.base import BaseStrategy, OrderType, StrategyContext


class MACrossoverStrategy(BaseStrategy):
    """移动均线交叉策略（经典双均线）."""

    name = "MA_Crossover"
    description = "快慢双均线交叉：金叉买入，死叉卖出"
    version = "1.0.0"

    default_params: dict[str, object] = {
        "fast_period": 10,
        "slow_period": 30,
        "trade_size": 0.95,  # 买入时使用资金比例
    }

    def on_init(self, context: StrategyContext) -> None:
        self._fast_window: deque[float] = deque(maxlen=int(
            self.get_param(context, "slow_period", 30)  # type: ignore[arg-type]
        ))
        self._slow_window: deque[float] = deque(maxlen=int(
            self.get_param(context, "slow_period", 30)  # type: ignore[arg-type]
        ))
        self._fast_period = int(self.get_param(context, "fast_period", 10))  # type: ignore[arg-type]
        self._slow_period = int(self.get_param(context, "slow_period", 30))  # type: ignore[arg-type]
        self._trade_size = float(self.get_param(context, "trade_size", 0.95))  # type: ignore[arg-type]

    def on_bar(self, bar: OHLCVBar, context: StrategyContext) -> None:
        self._fast_window.append(bar.close)
        self._slow_window.append(bar.close)

        if len(self._slow_window) < self._slow_period:
            return

        fast_ma = sum(list(self._fast_window)[-self._fast_period:]) / self._fast_period
        slow_ma = sum(self._slow_window) / self._slow_period

        position = context.get_position(bar.symbol)

        if fast_ma > slow_ma and (position is None or position.quantity <= 0):
            # 金叉买入
            shares = int(context.cash * self._trade_size / bar.close)
            if shares > 0:
                context.buy(bar.symbol, float(shares), OrderType.MARKET, comment="MA金叉买入")

        elif fast_ma < slow_ma and position is not None and position.quantity > 0:
            # 死叉卖出全部
            context.sell(
                bar.symbol, position.quantity, OrderType.MARKET, comment="MA死叉卖出"
            )
