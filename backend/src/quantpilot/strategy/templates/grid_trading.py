"""策略模板 5：网格交易策略.

信号逻辑：
  - 在价格区间 [low_price, high_price] 内均匀设置 N 个网格
  - 每下降一格买入固定手数，每上升一格卖出固定手数
  - 适合震荡市场，通过高抛低吸赚取价差
"""

from quantpilot.data.models import OHLCVBar
from quantpilot.strategy.base import BaseStrategy, OrderType, StrategyContext


class GridTradingStrategy(BaseStrategy):
    """网格交易策略."""

    name = "Grid_Trading"
    description = "均匀网格买低卖高，适合震荡行情"
    version = "1.0.0"

    default_params: dict[str, object] = {
        "grid_count": 10,         # 网格数量
        "price_low": 90.0,        # 网格下边界
        "price_high": 110.0,      # 网格上边界
        "shares_per_grid": 100.0, # 每格交易手数
    }

    def on_init(self, context: StrategyContext) -> None:
        self._n = int(self.get_param(context, "grid_count", 10))  # type: ignore[arg-type]
        self._low = float(self.get_param(context, "price_low", 90.0))  # type: ignore[arg-type]
        self._high = float(self.get_param(context, "price_high", 110.0))  # type: ignore[arg-type]
        self._shares = float(self.get_param(context, "shares_per_grid", 100.0))  # type: ignore[arg-type]

        # 计算网格价位
        step = (self._high - self._low) / self._n
        self._grids = [self._low + i * step for i in range(self._n + 1)]
        self._last_grid_index: int | None = None

    def _find_grid_index(self, price: float) -> int:
        """找到价格所在网格索引."""
        for i in range(len(self._grids) - 1):
            if self._grids[i] <= price < self._grids[i + 1]:
                return i
        return len(self._grids) - 2

    def on_bar(self, bar: OHLCVBar, context: StrategyContext) -> None:
        # 价格超出网格范围，不操作
        if bar.close < self._low or bar.close > self._high:
            return

        current_idx = self._find_grid_index(bar.close)

        if self._last_grid_index is None:
            self._last_grid_index = current_idx
            return

        if current_idx < self._last_grid_index:
            # 价格下降了一格或多格 → 买入
            diff = self._last_grid_index - current_idx
            buy_shares = self._shares * diff
            if context.cash >= buy_shares * bar.close:
                context.buy(bar.symbol, buy_shares, OrderType.MARKET,
                            comment=f"网格买入 grid={current_idx}")

        elif current_idx > self._last_grid_index:
            # 价格上升了一格或多格 → 卖出
            diff = current_idx - self._last_grid_index
            sell_shares = self._shares * diff
            position = context.get_position(bar.symbol)
            actual_sell = min(sell_shares, position.quantity if position else 0)
            if actual_sell > 0:
                context.sell(bar.symbol, actual_sell, OrderType.MARKET,
                             comment=f"网格卖出 grid={current_idx}")

        self._last_grid_index = current_idx
