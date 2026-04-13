"""策略模板 6：VWAP + 双 EMA 趋势策略.

信号逻辑：
  - 收盘价位于滚动 VWAP 之上，且快线 EMA > 慢线 EMA → 开多
  - 持仓期间根据最高价更新动态止损
  - 到达最大持仓 bar 数或跌破动态止损 → 卖出
"""

from collections import deque

from quantpilot.data.models import OHLCVBar
from quantpilot.strategy.base import BaseStrategy, OrderType, StrategyContext


class VWAPEMATrendStrategy(BaseStrategy):
    """使用 VWAP 过滤的双 EMA 趋势跟踪策略."""

    name = "VWAP_EMA_Trend"
    description = "VWAP 过滤震荡，双 EMA 确认趋势，支持动态止损与超时离场"
    version = "1.0.0"

    default_params: dict[str, object] = {
        "fast_period": 10,
        "slow_period": 30,
        "vwap_window": 20,
        "trade_size": 0.95,
        "max_hold_bars": 48,
        "trailing_stop_pct": 0.03,
    }

    def on_init(self, context: StrategyContext) -> None:
        self._fast_period = int(self.get_param(context, "fast_period", 10))  # type: ignore[arg-type]
        self._slow_period = int(self.get_param(context, "slow_period", 30))  # type: ignore[arg-type]
        self._vwap_window = int(self.get_param(context, "vwap_window", 20))  # type: ignore[arg-type]
        self._trade_size = float(self.get_param(context, "trade_size", 0.95))  # type: ignore[arg-type]
        self._max_hold_bars = int(self.get_param(context, "max_hold_bars", 48))  # type: ignore[arg-type]
        self._trailing_stop_pct = float(self.get_param(context, "trailing_stop_pct", 0.03))  # type: ignore[arg-type]

        max_window = max(self._slow_period, self._vwap_window)
        self._closes: deque[float] = deque(maxlen=max_window)
        self._volumes: deque[float] = deque(maxlen=max_window)
        self._hold_bars = 0
        self._peak_price = 0.0

    def on_bar(self, bar: OHLCVBar, context: StrategyContext) -> None:
        self._closes.append(bar.close)
        self._volumes.append(bar.volume)
        if len(self._closes) < max(self._slow_period, self._vwap_window):
            return

        closes = list(self._closes)
        volumes = list(self._volumes)
        fast_ema = self._ema(closes[-self._fast_period :], self._fast_period)
        slow_ema = self._ema(closes[-self._slow_period :], self._slow_period)
        vwap = self._rolling_vwap(closes[-self._vwap_window :], volumes[-self._vwap_window :])

        position = context.get_position(bar.symbol)

        if position is not None and position.quantity > 0:
            self._hold_bars += 1
            self._peak_price = max(self._peak_price, bar.close)
            trailing_stop = self._peak_price * (1 - self._trailing_stop_pct)
            if bar.close < trailing_stop:
                context.sell(
                    bar.symbol,
                    position.quantity,
                    OrderType.MARKET,
                    comment=f"VWAP_EMA 动态止损 close={bar.close:.2f} stop={trailing_stop:.2f}",
                )
                self._hold_bars = 0
                self._peak_price = 0.0
                return

            if self._hold_bars >= self._max_hold_bars:
                context.sell(
                    bar.symbol,
                    position.quantity,
                    OrderType.MARKET,
                    comment=f"VWAP_EMA 超时离场 hold={self._hold_bars}",
                )
                self._hold_bars = 0
                self._peak_price = 0.0
                return

        bullish_trend = bar.close > vwap and fast_ema > slow_ema
        if bullish_trend and (position is None or position.quantity <= 0):
            shares = int(context.cash * self._trade_size / bar.close)
            if shares > 0:
                context.buy(
                    bar.symbol,
                    float(shares),
                    OrderType.MARKET,
                    comment=f"VWAP_EMA 趋势入场 close={bar.close:.2f} vwap={vwap:.2f}",
                )
                self._hold_bars = 0
                self._peak_price = bar.close

    def _rolling_vwap(self, closes: list[float], volumes: list[float]) -> float:
        total_volume = sum(volumes)
        if total_volume <= 0:
            return closes[-1]
        return sum(price * volume for price, volume in zip(closes, volumes, strict=True)) / total_volume

    def _ema(self, closes: list[float], period: int) -> float:
        alpha = 2 / (period + 1)
        value = closes[0]
        for close in closes[1:]:
            value = alpha * close + (1 - alpha) * value
        return value
