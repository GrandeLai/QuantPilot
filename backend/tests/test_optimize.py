"""策略参数优化测试 — T-3.5 验收."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from quantpilot.backtest.engine import BacktestConfig
from quantpilot.data.models import OHLCVBar
from quantpilot.optimize.engine import OptimizationEngine, OptimizeResult, ParamGrid
from quantpilot.strategy.base import BaseStrategy, StrategyContext


def _bar(i: int, price: float = 100.0) -> OHLCVBar:
    return OHLCVBar(
        symbol="TEST",
        timeframe="1d",
        timestamp=datetime(2024, 1, 1, tzinfo=UTC) + timedelta(days=i),
        open=price * 0.99,
        high=price * 1.01,
        low=price * 0.98,
        close=price,
        volume=1_000_000,
    )


class SMAStrategy(BaseStrategy):
    """简单双均线策略，用于参数优化测试."""

    name = "sma_test"
    description = "SMA crossover for optimization test"

    def __init__(self, fast: int = 5, slow: int = 20) -> None:
        self.fast = fast
        self.slow = slow
        self._prices: list[float] = []

    def on_bar(self, bar: OHLCVBar, context: StrategyContext) -> None:
        self._prices.append(bar.close)
        if len(self._prices) < self.slow:
            return
        fast_ma = sum(self._prices[-self.fast :]) / self.fast
        slow_ma = sum(self._prices[-self.slow :]) / self.slow
        if fast_ma > slow_ma and not context.positions:
            context.buy(bar.symbol, 10, bar.close)
        elif fast_ma < slow_ma and context.positions:
            context.sell(bar.symbol, 10, bar.close)


class TestParamGrid:
    def test_grid_size(self) -> None:
        grid = ParamGrid({"fast": [3, 5, 10], "slow": [20, 30]})
        combos = list(grid.combinations())
        assert len(combos) == 6  # 3 × 2

    def test_grid_values(self) -> None:
        grid = ParamGrid({"a": [1, 2], "b": [10]})
        combos = list(grid.combinations())
        assert {"a": 1, "b": 10} in combos
        assert {"a": 2, "b": 10} in combos


class TestOptimizationEngine:
    @pytest.fixture
    def bars(self) -> list[OHLCVBar]:
        return [_bar(i, 100.0 + i * 0.1) for i in range(60)]

    @pytest.fixture
    def config(self) -> BacktestConfig:
        return BacktestConfig(symbol="TEST", timeframe="1d", initial_cash=100_000.0)

    def test_grid_search_returns_results(
        self, bars: list[OHLCVBar], config: BacktestConfig
    ) -> None:
        engine = OptimizationEngine(config, bars)
        grid = ParamGrid({"fast": [3, 5], "slow": [10, 15]})
        results = engine.grid_search(
            strategy_class=SMAStrategy,
            param_grid=grid,
        )
        assert isinstance(results, list)
        assert len(results) == 4  # 2 × 2

    def test_best_result_has_highest_sharpe(
        self, bars: list[OHLCVBar], config: BacktestConfig
    ) -> None:
        engine = OptimizationEngine(config, bars)
        grid = ParamGrid({"fast": [3, 5], "slow": [10, 15]})
        results = engine.grid_search(SMAStrategy, grid)
        best = max(results, key=lambda r: r.sharpe_ratio)
        assert results[0].sharpe_ratio == best.sharpe_ratio
        assert isinstance(best, OptimizeResult)

    def test_bayesian_search(
        self, bars: list[OHLCVBar], config: BacktestConfig
    ) -> None:
        engine = OptimizationEngine(config, bars)
        param_space = {"fast": (2, 8), "slow": (10, 20)}
        result = engine.bayesian_search(SMAStrategy, param_space, n_trials=5)
        assert isinstance(result, OptimizeResult)
        assert isinstance(result.sharpe_ratio, float)
        assert 2 <= result.params["fast"] <= 8
        assert 10 <= result.params["slow"] <= 20
