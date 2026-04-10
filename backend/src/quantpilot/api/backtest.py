"""回测 API 路由.

端点：
  POST /backtest/run    提交回测任务
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from quantpilot.backtest.engine import BacktestConfig, BacktestEngine
from quantpilot.data.models import OHLCVBar
from quantpilot.strategy.templates import TEMPLATE_STRATEGIES

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


@router.post("/run", response_model=BacktestResponse)
def run_backtest(req: BacktestRequest) -> BacktestResponse:
    """执行回测并返回绩效指标."""
    if len(req.bars) < 2:
        raise HTTPException(status_code=400, detail="至少需要 2 根 K 线才能运行回测")

    # 加载策略
    if req.strategy_id not in TEMPLATE_STRATEGIES:
        raise HTTPException(
            status_code=400,
            detail=f"未知策略: {req.strategy_id}，可用模板: {list(TEMPLATE_STRATEGIES.keys())}",
        )

    strategy_cls = TEMPLATE_STRATEGIES[req.strategy_id]
    strategy = strategy_cls()

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
