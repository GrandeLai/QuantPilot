"""策略模板 2：RSI 均值回归策略.

信号逻辑：
  - RSI < 超卖阈值 → 买入（预期反弹）
  - RSI > 超买阈值 → 卖出（预期回落）
"""

from collections import deque

from quantpilot_common.data.models import OHLCVBar
from quantpilot.strategy.base import BaseStrategy, OrderType, StrategyContext


class RSIMeanReversionStrategy(BaseStrategy):
    """RSI 均值回归策略."""

    name = "RSI_Mean_Reversion"
    description = "RSI 超卖买入，超买卖出"
    version = "1.0.0"

    default_params: dict[str, object] = {
        "rsi_period": 14,
        "oversold": 30,
        "overbought": 70,
        "trade_size": 0.95,
    }

    def on_init(self, context: StrategyContext) -> None:
        self._period = int(self.get_param(context, "rsi_period", 14))  # type: ignore[arg-type]
        self._oversold = float(self.get_param(context, "oversold", 30))  # type: ignore[arg-type]
        self._overbought = float(self.get_param(context, "overbought", 70))  # type: ignore[arg-type]
        self._trade_size = float(self.get_param(context, "trade_size", 0.95))  # type: ignore[arg-type]
        self._closes: deque[float] = deque(maxlen=self._period + 1)

    def _calc_rsi(self) -> float | None:
        closes = list(self._closes)
        if len(closes) < self._period + 1:
            return None
        gains, losses = [], []
        for i in range(1, len(closes)):
            delta = closes[i] - closes[i - 1]
            if delta > 0:
                gains.append(delta)
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(abs(delta))
        avg_gain = sum(gains) / self._period
        avg_loss = sum(losses) / self._period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1 + rs))

    def on_bar(self, bar: OHLCVBar, context: StrategyContext) -> None:
        self._closes.append(bar.close)
        rsi = self._calc_rsi()
        if rsi is None:
            return

        position = context.get_position(bar.symbol)

        if rsi < self._oversold and (position is None or position.quantity <= 0):
            shares = int(context.cash * self._trade_size / bar.close)
            if shares > 0:
                context.buy(bar.symbol, float(shares), OrderType.MARKET,
                            comment=f"RSI超卖买入 RSI={rsi:.1f}")

        elif rsi > self._overbought and position is not None and position.quantity > 0:
            context.sell(bar.symbol, position.quantity, OrderType.MARKET,
                         comment=f"RSI超买卖出 RSI={rsi:.1f}")
