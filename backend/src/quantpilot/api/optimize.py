"""参数优化 API.

端点:
  POST /optimize/grid-search    网格搜索优化
  POST /optimize/bayesian       Optuna 贝叶斯优化
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from quantpilot.backtest.engine import BacktestConfig
from quantpilot_common.data.models import OHLCVBar
from quantpilot.optimize.engine import OptimizationEngine, ParamGrid

router = APIRouter(prefix="/optimize", tags=["参数优化"])


class OHLCVBarInput(BaseModel):
    symbol: str
    timeframe: str
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class GridSearchRequest(BaseModel):
    strategy_name: str
    config: BacktestConfig
    bars: list[OHLCVBarInput]
    param_grid: dict[str, list[Any]]


class BayesianSearchRequest(BaseModel):
    strategy_name: str
    config: BacktestConfig
    bars: list[OHLCVBarInput]
    param_space: dict[str, list[int]]
    n_trials: int = 30


def _resolve_strategy(name: str) -> type:
    from quantpilot.strategy.loader import load_strategy_class

    cls = load_strategy_class(name)
    if cls is None:
        raise HTTPException(status_code=404, detail=f"策略 '{name}' 未找到")
    return cls


def _to_bars(bar_inputs: list[OHLCVBarInput]) -> list[OHLCVBar]:
    bars = []
    for b in bar_inputs:
        bars.append(
            OHLCVBar(
                symbol=b.symbol,
                timeframe=b.timeframe,
                timestamp=datetime.fromisoformat(b.timestamp).replace(tzinfo=UTC),
                open=b.open,
                high=b.high,
                low=b.low,
                close=b.close,
                volume=b.volume,
            )
        )
    return bars


@router.post("/grid-search")
def grid_search(req: GridSearchRequest) -> dict[str, Any]:
    """对策略参数做网格搜索，返回所有组合结果."""
    strategy_cls = _resolve_strategy(req.strategy_name)
    bars = _to_bars(req.bars)
    engine = OptimizationEngine(req.config, bars)
    grid = ParamGrid(req.param_grid)
    results = engine.grid_search(strategy_cls, grid)
    return {
        "total_combinations": len(results),
        "best": {
            "params": results[0].params,
            "sharpe_ratio": results[0].sharpe_ratio,
            "total_return": results[0].total_return,
        },
        "results": [
            {"params": r.params, "sharpe_ratio": r.sharpe_ratio, "total_return": r.total_return}
            for r in results[:20]
        ],
    }


@router.post("/bayesian")
def bayesian_search(req: BayesianSearchRequest) -> dict[str, Any]:
    """Optuna 贝叶斯优化."""
    strategy_cls = _resolve_strategy(req.strategy_name)
    bars = _to_bars(req.bars)
    engine = OptimizationEngine(req.config, bars)
    param_space = {k: (v[0], v[1]) for k, v in req.param_space.items()}
    result = engine.bayesian_search(strategy_cls, param_space, n_trials=req.n_trials)
    return {
        "best_params": result.params,
        "sharpe_ratio": result.sharpe_ratio,
        "total_return": result.total_return,
        "max_drawdown": result.max_drawdown,
        "total_trades": result.total_trades,
    }
