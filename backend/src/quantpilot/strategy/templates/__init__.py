"""5 个内置策略模板."""

from quantpilot.strategy.templates.bollinger_breakout import BollingerBreakoutStrategy
from quantpilot.strategy.templates.grid_trading import GridTradingStrategy
from quantpilot.strategy.templates.ma_crossover import MACrossoverStrategy
from quantpilot.strategy.templates.momentum import MomentumStrategy
from quantpilot.strategy.templates.rsi_mean_reversion import RSIMeanReversionStrategy
from quantpilot.strategy.templates.vwap_ema_trend import VWAPEMATrendStrategy

TEMPLATE_STRATEGIES: dict[str, type] = {
    "ma_crossover": MACrossoverStrategy,
    "rsi_mean_reversion": RSIMeanReversionStrategy,
    "bollinger_breakout": BollingerBreakoutStrategy,
    "momentum": MomentumStrategy,
    "grid_trading": GridTradingStrategy,
    "vwap_ema_trend": VWAPEMATrendStrategy,
}

__all__ = [
    "MACrossoverStrategy",
    "RSIMeanReversionStrategy",
    "BollingerBreakoutStrategy",
    "MomentumStrategy",
    "GridTradingStrategy",
    "VWAPEMATrendStrategy",
    "TEMPLATE_STRATEGIES",
]
