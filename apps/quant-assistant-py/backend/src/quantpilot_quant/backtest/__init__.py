"""回测引擎模块."""

from quantpilot_quant.backtest.engine import BacktestConfig, BacktestEngine, BacktestResult
from quantpilot_quant.backtest.metrics import BacktestMetrics, TradeRecord, calculate_metrics
from quantpilot_quant.backtest.walk_forward import (
    WalkForwardConfig,
    WalkForwardEngine,
    WalkForwardResult,
    WalkForwardWindowResult,
)

__all__ = [
    "BacktestConfig",
    "BacktestEngine",
    "BacktestResult",
    "BacktestMetrics",
    "TradeRecord",
    "calculate_metrics",
    "WalkForwardConfig",
    "WalkForwardEngine",
    "WalkForwardResult",
    "WalkForwardWindowResult",
]
