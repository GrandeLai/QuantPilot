"""策略模板 4：动量策略.

信号逻辑：
  - N 日收益率超过阈值 → 买入（趋势延续）
  - 收益率低于负阈值或持仓超过最大持有期 → 卖出
"""

from collections import deque

from quantpilot.data.models import OHLCVBar
from quantpilot.strategy.base import BaseStrategy, OrderType, StrategyContext


class MomentumStrategy(BaseStrategy):
    """价格动量策略."""

    name = "Momentum"
    description = "N 日涨幅超过阈值买入，跌幅超过阈值或持仓期到达时卖出"
    version = "1.0.0"

    default_params: dict[str, object] = {
        "lookback": 20,          # 动量计算回看期
        "buy_threshold": 0.05,   # 买入阈值（+5%）
        "sell_threshold": -0.03, # 卖出阈值（-3%）
        "max_hold_days": 30,     # 最大持仓天数
        "trade_size": 0.95,
    }

    def on_init(self, context: StrategyContext) -> None:
        self._lookback = int(self.get_param(context, "lookback", 20))  # type: ignore[arg-type]
        self._buy_th = float(self.get_param(context, "buy_threshold", 0.05))  # type: ignore[arg-type]
        self._sell_th = float(self.get_param(context, "sell_threshold", -0.03))  # type: ignore[arg-type]
        self._max_hold = int(self.get_param(context, "max_hold_days", 30))  # type: ignore[arg-type]
        self._trade_size = float(self.get_param(context, "trade_size", 0.95))  # type: ignore[arg-type]
        self._closes: deque[float] = deque(maxlen=self._lookback + 1)
        self._hold_days = 0

    def on_bar(self, bar: OHLCVBar, context: StrategyContext) -> None:
        self._closes.append(bar.close)
        if len(self._closes) < self._lookback + 1:
            return

        closes = list(self._closes)
        momentum = (closes[-1] - closes[0]) / closes[0]  # N日收益率

        position = context.get_position(bar.symbol)

        if position is not None and position.quantity > 0:
            self._hold_days += 1
            current_return = (bar.close - position.avg_price) / position.avg_price
            if current_return < self._sell_th or self._hold_days >= self._max_hold:
                context.sell(bar.symbol, position.quantity, OrderType.MARKET,
                             comment=f"动量止损/持仓到期 ret={current_return:.2%}")
                self._hold_days = 0
        elif momentum > self._buy_th and (position is None or position.quantity <= 0):
            shares = int(context.cash * self._trade_size / bar.close)
            if shares > 0:
                context.buy(bar.symbol, float(shares), OrderType.MARKET,
                            comment=f"动量买入 momentum={momentum:.2%}")
                self._hold_days = 0
