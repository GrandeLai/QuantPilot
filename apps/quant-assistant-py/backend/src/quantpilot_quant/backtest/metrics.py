"""回测绩效指标计算.

支持：Sharpe Ratio、Max Drawdown、Calmar Ratio、Win Rate、
      Profit Factor、Sortino Ratio、年化收益率等。

TradeRecord 数据契约已下沉到 ``quantpilot_common.contracts.trade``；
本模块从那里 re-export 以保持向后兼容。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from quantpilot_common.contracts.trade import TradeRecord

__all__ = ["TradeRecord", "BacktestMetrics", "calculate_metrics"]


@dataclass
class BacktestMetrics:
    """回测绩效指标汇总."""

    # 收益类
    initial_cash: float = 0.0
    final_value: float = 0.0
    total_return: float = 0.0        # 总收益率
    annual_return: float = 0.0       # 年化收益率
    # 风险类
    max_drawdown: float = 0.0        # 最大回撤（负值）
    max_drawdown_duration: int = 0   # 最大回撤持续天数
    volatility: float = 0.0          # 年化波动率
    # 风险调整收益
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    # 交易统计
    total_trades: int = 0
    win_trades: int = 0
    loss_trades: int = 0
    win_rate: float = 0.0            # 胜率
    profit_factor: float = 0.0      # 盈亏比
    avg_win: float = 0.0
    avg_loss: float = 0.0
    # 时间信息
    start_date: str = ""
    end_date: str = ""
    trading_days: int = 0
    # 净值序列（每日）
    portfolio_values: list[float] = field(default_factory=list)
    daily_returns: list[float] = field(default_factory=list)


def calculate_metrics(
    portfolio_values: list[float],
    trades: list[TradeRecord],
    initial_cash: float,
    risk_free_rate: float = 0.02,
    periods_per_year: int = 252,
) -> BacktestMetrics:
    """计算回测绩效指标.

    Args:
        portfolio_values: 每日组合净值序列
        trades: 已平仓交易记录
        initial_cash: 初始资金
        risk_free_rate: 年化无风险利率
        periods_per_year: 每年交易天数

    Returns:
        BacktestMetrics 实例
    """
    metrics = BacktestMetrics(
        initial_cash=initial_cash,
        portfolio_values=portfolio_values,
    )

    if not portfolio_values or len(portfolio_values) < 2:
        return metrics

    # ── 收益计算 ──────────────────────────────────────────────────────────────
    metrics.final_value = portfolio_values[-1]
    metrics.total_return = (metrics.final_value - initial_cash) / initial_cash
    metrics.trading_days = len(portfolio_values)

    years = metrics.trading_days / periods_per_year
    if years > 0:
        metrics.annual_return = (1 + metrics.total_return) ** (1 / years) - 1

    # ── 日收益率序列 ──────────────────────────────────────────────────────────
    daily_returns = [
        (portfolio_values[i] - portfolio_values[i - 1]) / portfolio_values[i - 1]
        for i in range(1, len(portfolio_values))
    ]
    metrics.daily_returns = daily_returns

    if not daily_returns:
        return metrics

    n = len(daily_returns)
    mean_ret = sum(daily_returns) / n
    variance = sum((r - mean_ret) ** 2 for r in daily_returns) / max(n - 1, 1)
    std_dev = math.sqrt(variance)

    # ── 波动率 ────────────────────────────────────────────────────────────────
    metrics.volatility = std_dev * math.sqrt(periods_per_year)

    # ── Sharpe Ratio ──────────────────────────────────────────────────────────
    daily_rf = risk_free_rate / periods_per_year
    if std_dev > 0:
        metrics.sharpe_ratio = (mean_ret - daily_rf) / std_dev * math.sqrt(periods_per_year)

    # ── Sortino Ratio（只用下行波动）─────────────────────────────────────────
    downside_returns = [r for r in daily_returns if r < daily_rf]
    if downside_returns:
        downside_var = sum((r - daily_rf) ** 2 for r in downside_returns) / len(downside_returns)
        downside_std = math.sqrt(downside_var)
        if downside_std > 0:
            metrics.sortino_ratio = (
                (mean_ret - daily_rf) / downside_std * math.sqrt(periods_per_year)
            )

    # ── 最大回撤 ──────────────────────────────────────────────────────────────
    peak = portfolio_values[0]
    max_dd = 0.0
    dd_start = 0
    dd_start_idx = 0
    max_dd_duration = 0

    for i, val in enumerate(portfolio_values):
        if val > peak:
            peak = val
            dd_start_idx = i
        dd = (peak - val) / peak
        if dd > max_dd:
            max_dd = dd
            dd_start = dd_start_idx
            max_dd_duration = i - dd_start

    metrics.max_drawdown = -max_dd
    metrics.max_drawdown_duration = max_dd_duration

    # ── Calmar Ratio ──────────────────────────────────────────────────────────
    if max_dd > 0:
        metrics.calmar_ratio = metrics.annual_return / max_dd

    # ── 交易统计 ──────────────────────────────────────────────────────────────
    metrics.total_trades = len(trades)
    if trades:
        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl <= 0]
        metrics.win_trades = len(wins)
        metrics.loss_trades = len(losses)
        metrics.win_rate = metrics.win_trades / metrics.total_trades

        total_profit = sum(t.pnl for t in wins)
        total_loss = abs(sum(t.pnl for t in losses))

        metrics.avg_win = total_profit / len(wins) if wins else 0.0
        metrics.avg_loss = total_loss / len(losses) if losses else 0.0
        metrics.profit_factor = total_profit / total_loss if total_loss > 0 else float("inf")

    return metrics
