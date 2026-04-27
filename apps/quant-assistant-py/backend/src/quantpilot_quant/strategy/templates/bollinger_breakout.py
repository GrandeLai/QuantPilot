"""策略模板 3：布林带突破策略.

信号逻辑：
  - 价格突破上轨 → 买入（强势突破）
  - 价格跌破下轨 → 卖出（趋势反转）
  - 价格回到中轨 → 平仓止盈
"""

from collections import deque

from quantpilot_common.data.models import OHLCVBar
from quantpilot_quant.strategy.base import BaseStrategy, OrderType, StrategyContext


class BollingerBreakoutStrategy(BaseStrategy):
    """布林带突破策略."""

    name = "Bollinger_Breakout"
    description = "价格突破布林带上轨买入，跌破下轨或回到中轨平仓"
    version = "1.0.0"

    default_params: dict[str, object] = {
        "period": 20,
        "std_dev": 2.0,
        "trade_size": 0.95,
    }

    def on_init(self, context: StrategyContext) -> None:
        self._period = int(self.get_param(context, "period", 20))  # type: ignore[arg-type]
        self._std_dev = float(self.get_param(context, "std_dev", 2.0))  # type: ignore[arg-type]
        self._trade_size = float(self.get_param(context, "trade_size", 0.95))  # type: ignore[arg-type]
        self._closes: deque[float] = deque(maxlen=self._period)

    def _calc_bands(self) -> tuple[float, float, float] | None:
        if len(self._closes) < self._period:
            return None
        closes = list(self._closes)
        mid = sum(closes) / self._period
        variance = sum((c - mid) ** 2 for c in closes) / self._period
        std = variance ** 0.5
        return mid - self._std_dev * std, mid, mid + self._std_dev * std

    def on_bar(self, bar: OHLCVBar, context: StrategyContext) -> None:
        self._closes.append(bar.close)
        bands = self._calc_bands()
        if bands is None:
            return
        lower, mid, upper = bands
        position = context.get_position(bar.symbol)

        if bar.close > upper and (position is None or position.quantity <= 0):
            shares = int(context.cash * self._trade_size / bar.close)
            if shares > 0:
                context.buy(bar.symbol, float(shares), OrderType.MARKET,
                            comment=f"突破布林上轨买入 upper={upper:.2f}")

        elif position is not None and position.quantity > 0:
            if bar.close < lower or bar.close < mid:
                context.sell(bar.symbol, position.quantity, OrderType.MARKET,
                             comment="布林带平仓")
