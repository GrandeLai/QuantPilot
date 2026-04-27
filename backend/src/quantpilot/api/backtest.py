"""回测 API 路由.

端点：
  POST /backtest/run             提交回测任务
  POST /backtest/walk-forward    Walk-Forward 滚动步进回测
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from quantpilot.backtest.engine import BacktestConfig, BacktestEngine
from quantpilot.backtest.walk_forward import WalkForwardConfig, WalkForwardEngine
from quantpilot.data.models import OHLCVBar
from quantpilot.strategy.loader import load_strategy_class

router = APIRouter(prefix="/backtest", tags=["回测"])


class BacktestRequest(BaseModel):
    """回测请求参数."""

    symbol: str
    timeframe: str = "1d"
    bars: list[OHLCVBar]
    strategy_id: str  # 模板策略 ID 或用户策略 ID
    strategy_params: dict[str, Any] = {}
    initial_cash: float = 1_000_000.0
    commission_rate: float = 0.001
    slippage_pct: float = 0.0005
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None


class BacktestResponse(BaseModel):
    """回测响应."""

    symbol: str
    timeframe: str
    strategy_id: str
    bars_processed: int
    duration_seconds: float
    metrics: dict[str, Any]
    trades_count: int


class WalkForwardRequest(BaseModel):
    """Walk-Forward 回测请求."""

    symbol: str
    timeframe: str = "1d"
    bars: list[OHLCVBar]
    strategy_id: str
    strategy_params: dict[str, Any] = {}
    initial_cash: float = 1_000_000.0
    commission_rate: float = 0.001
    slippage_pct: float = 0.0005
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None
    # Walk-Forward 专属参数
    train_size: int = 252
    test_size: int = 63
    step_size: int = 21
    gap_size: int = 5
    param_grid: dict[str, list[Any]] = {}


class WalkForwardWindowSummary(BaseModel):
    """单窗口回测摘要."""

    window_idx: int
    train_range: tuple[int, int]
    gap_range: tuple[int, int]
    test_range: tuple[int, int]
    best_params: dict[str, Any]
    metrics: dict[str, Any]
    trades_count: int


class WalkForwardResponse(BaseModel):
    """Walk-Forward 回测响应."""

    symbol: str
    timeframe: str
    strategy_id: str
    n_windows: int
    total_bars: int
    duration_seconds: float
    aggregated_metrics: dict[str, Any]
    windows: list[WalkForwardWindowSummary]


@router.post("/walk-forward", response_model=WalkForwardResponse)
def run_walk_forward(req: WalkForwardRequest) -> WalkForwardResponse:
    """执行 Walk-Forward 滚动步进回测."""
    min_bars = req.train_size + req.gap_size + req.test_size
    if len(req.bars) < min_bars:
        raise HTTPException(
            status_code=400,
            detail=f"K 线数量不足：{len(req.bars)} 根，至少需要 {min_bars} 根",
        )

    strategy_cls = load_strategy_class(req.strategy_id)
    if strategy_cls is None:
        raise HTTPException(status_code=400, detail=f"未知策略: {req.strategy_id}")

    config = BacktestConfig(
        symbol=req.symbol,
        timeframe=req.timeframe,
        initial_cash=req.initial_cash,
        commission_rate=req.commission_rate,
        slippage_pct=req.slippage_pct,
        stop_loss_pct=req.stop_loss_pct,
        take_profit_pct=req.take_profit_pct,
    )
    wf_config = WalkForwardConfig(
        train_size=req.train_size,
        test_size=req.test_size,
        step_size=req.step_size,
        gap_size=req.gap_size,
    )

    engine = WalkForwardEngine(config, wf_config)
    result = engine.run(
        strategy_cls,
        req.bars,
        param_grid=req.param_grid or None,
    )

    def _metrics_dict(m: Any) -> dict[str, Any]:
        return {
            "total_return": m.total_return,
            "annual_return": m.annual_return,
            "max_drawdown": m.max_drawdown,
            "sharpe_ratio": m.sharpe_ratio,
            "sortino_ratio": m.sortino_ratio,
            "calmar_ratio": m.calmar_ratio,
            "volatility": m.volatility,
            "win_rate": m.win_rate,
            "profit_factor": m.profit_factor,
            "total_trades": m.total_trades,
            "win_trades": m.win_trades,
            "loss_trades": m.loss_trades,
            "avg_win": m.avg_win,
            "avg_loss": m.avg_loss,
            "initial_cash": m.initial_cash,
            "final_value": m.final_value,
            "start_date": m.start_date,
            "end_date": m.end_date,
            "trading_days": m.trading_days,
        }

    windows = [
        WalkForwardWindowSummary(
            window_idx=wr.window_idx,
            train_range=wr.train_range,
            gap_range=wr.gap_range,
            test_range=wr.test_range,
            best_params=wr.best_params,
            metrics=_metrics_dict(wr.result.metrics),
            trades_count=wr.result.metrics.total_trades,
        )
        for wr in result.windows
    ]

    return WalkForwardResponse(
        symbol=req.symbol,
        timeframe=req.timeframe,
        strategy_id=req.strategy_id,
        n_windows=result.n_windows,
        total_bars=len(req.bars),
        duration_seconds=result.duration_seconds,
        aggregated_metrics=_metrics_dict(result.aggregated_metrics),
        windows=windows,
    )


@router.post("/run", response_model=BacktestResponse)
def run_backtest(req: BacktestRequest) -> BacktestResponse:
    """执行回测并返回绩效指标."""
    if len(req.bars) < 2:
        raise HTTPException(status_code=400, detail="至少需要 2 根 K 线才能运行回测")

    # 加载策略
    strategy_cls = load_strategy_class(req.strategy_id)
    if strategy_cls is None:
        raise HTTPException(
            status_code=400,
            detail=f"未知策略: {req.strategy_id}",
        )

    strategy = strategy_cls()
    if req.strategy_params:
        strategy.default_params = {**strategy.default_params, **req.strategy_params}

    config = BacktestConfig(
        symbol=req.symbol,
        timeframe=req.timeframe,
        initial_cash=req.initial_cash,
        commission_rate=req.commission_rate,
        slippage_pct=req.slippage_pct,
        stop_loss_pct=req.stop_loss_pct,
        take_profit_pct=req.take_profit_pct,
    )

    engine = BacktestEngine(config)
    result = engine.run(strategy, req.bars)

    m = result.metrics
    return BacktestResponse(
        symbol=req.symbol,
        timeframe=req.timeframe,
        strategy_id=req.strategy_id,
        bars_processed=result.bars_processed,
        duration_seconds=result.duration_seconds,
        trades_count=result.metrics.total_trades,
        metrics={
            "total_return": m.total_return,
            "annual_return": m.annual_return,
            "max_drawdown": m.max_drawdown,
            "sharpe_ratio": m.sharpe_ratio,
            "sortino_ratio": m.sortino_ratio,
            "calmar_ratio": m.calmar_ratio,
            "volatility": m.volatility,
            "win_rate": m.win_rate,
            "profit_factor": m.profit_factor,
            "total_trades": m.total_trades,
            "win_trades": m.win_trades,
            "loss_trades": m.loss_trades,
            "avg_win": m.avg_win,
            "avg_loss": m.avg_loss,
            "initial_cash": m.initial_cash,
            "final_value": m.final_value,
            "start_date": m.start_date,
            "end_date": m.end_date,
            "trading_days": m.trading_days,
        },
    )
