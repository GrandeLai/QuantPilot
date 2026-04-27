"""策略参数优化引擎 — 网格搜索 + Optuna 贝叶斯优化."""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from loguru import logger

from quantpilot.backtest.engine import BacktestConfig, BacktestEngine
from quantpilot_common.data.models import OHLCVBar

if TYPE_CHECKING:
    from quantpilot.strategy.base import BaseStrategy


@dataclass
class OptimizeResult:
    """单次参数组合回测结果."""

    params: dict[str, Any]
    sharpe_ratio: float
    total_return: float
    max_drawdown: float
    total_trades: int


class ParamGrid:
    """参数网格定义."""

    def __init__(self, grid: dict[str, list[Any]]) -> None:
        self._grid = grid

    def combinations(self) -> list[dict[str, Any]]:
        """返回所有参数组合."""
        keys = list(self._grid.keys())
        values = list(self._grid.values())
        return [dict(zip(keys, combo, strict=True)) for combo in itertools.product(*values)]


class OptimizationEngine:
    """策略参数优化引擎."""

    def __init__(self, config: BacktestConfig, bars: list[OHLCVBar]) -> None:
        self._config = config
        self._bars = bars

    def _run_single(
        self,
        strategy_class: type[BaseStrategy],
        params: dict[str, Any],
    ) -> OptimizeResult:
        """运行单次回测，返回优化结果."""
        try:
            try:
                strategy = strategy_class(**params)
            except TypeError:
                strategy = strategy_class()
                strategy.default_params = {**getattr(strategy, "default_params", {}), **params}
            engine = BacktestEngine(self._config)
            result = engine.run(strategy, self._bars)
            return OptimizeResult(
                params=params,
                sharpe_ratio=result.metrics.sharpe_ratio,
                total_return=result.metrics.total_return,
                max_drawdown=result.metrics.max_drawdown,
                total_trades=result.metrics.total_trades,
            )
        except Exception as e:
            logger.warning(f"[Optimize] params={params} failed: {e}")
            return OptimizeResult(
                params=params,
                sharpe_ratio=-999.0,
                total_return=0.0,
                max_drawdown=0.0,
                total_trades=0,
            )

    def grid_search(
        self,
        strategy_class: type[BaseStrategy],
        param_grid: ParamGrid,
    ) -> list[OptimizeResult]:
        """穷举所有参数组合，返回所有结果（按 Sharpe 降序）."""
        combos = param_grid.combinations()
        results = [self._run_single(strategy_class, params) for params in combos]
        results.sort(key=lambda r: r.sharpe_ratio, reverse=True)
        if not results:
            return []
        logger.info(
            f"[Optimize] grid search: {len(results)} combos, best sharpe={results[0].sharpe_ratio:.3f}"
        )
        return results

    def bayesian_search(
        self,
        strategy_class: type[BaseStrategy],
        param_space: dict[str, tuple[int, int]],
        n_trials: int = 50,
    ) -> OptimizeResult:
        """Optuna TPE 贝叶斯优化，返回最优参数组合.

        param_space: {param_name: (low, high)} for integer params
        """
        import optuna

        optuna.logging.set_verbosity(optuna.logging.WARNING)

        def objective(trial: optuna.Trial) -> float:
            params = {
                name: trial.suggest_int(name, low, high)
                for name, (low, high) in param_space.items()
            }
            result = self._run_single(strategy_class, params)
            return result.sharpe_ratio

        study = optuna.create_study(direction="maximize")
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

        best_params = study.best_params
        best_result = self._run_single(strategy_class, best_params)
        logger.info(
            f"[Optimize] bayesian: best params={best_params}, sharpe={best_result.sharpe_ratio:.3f}"
        )
        return best_result
