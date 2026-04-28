"""MA crossover golden case.

实现与 Rust ``apps/quant-assistant/backend/src/lib.rs::run_ma_crossover_backtest``
**逐行对齐**的 Python 算法（不是 quant-py 的 BaseStrategy 引擎）。
用于跨语言 bit-equivalent 验证。
"""

from __future__ import annotations

import math
from typing import Any


def python_ma_crossover_backtest(
    closes: list[float],
    fast_period: int,
    slow_period: int,
    initial_cash: float,
) -> list[float]:
    """与 Rust run_ma_crossover_backtest 对齐的 Python 实现.

    注意：求和顺序、除法顺序、比较顺序必须与 Rust 一致，否则浮点精度会偏离。
    """
    n = len(closes)
    if n < slow_period:
        raise ValueError(f"数据长度不足：需要至少 {slow_period} 个数据点，实际 {n}")

    portfolio_values = [initial_cash] * n
    position = 0.0
    cash = initial_cash

    for i in range(slow_period, n):
        # Rust: closes[(i - fast_period)..i].iter().sum() — 左到右累加
        fast_sum = sum(closes[i - fast_period : i])
        fast_ma = fast_sum / fast_period

        slow_sum = sum(closes[i - slow_period : i])
        slow_ma = slow_sum / slow_period

        price = closes[i]

        if fast_ma > slow_ma and position == 0.0 and cash > 0.0:
            position = cash / price
            cash = 0.0
        elif fast_ma < slow_ma and position > 0.0:
            cash = position * price
            position = 0.0

        portfolio_values[i] = cash + position * price

    # First slow_period values reset to initial_cash
    for i in range(slow_period):
        portfolio_values[i] = initial_cash

    return portfolio_values


def python_sharpe_ratio(
    returns: list[float],
    risk_free_rate: float,
    periods_per_year: float,
) -> float:
    """与 Rust sharpe_ratio 对齐."""
    n = len(returns)
    if n < 2:
        return 0.0

    mean = sum(returns) / n
    variance = sum((r - mean) ** 2 for r in returns) / (n - 1)
    std_dev = math.sqrt(variance)

    if std_dev == 0.0:
        return 0.0

    daily_rf = risk_free_rate / periods_per_year
    return (mean - daily_rf) / std_dev * math.sqrt(periods_per_year)


def python_max_drawdown(portfolio_values: list[float]) -> tuple[float, int, int]:
    """与 Rust max_drawdown 对齐."""
    n = len(portfolio_values)
    if n < 2:
        return (0.0, 0, 0)

    max_dd = 0.0
    peak = portfolio_values[0]
    peak_idx = 0
    dd_start = 0
    dd_end = 0

    for i in range(1, n):
        value = portfolio_values[i]
        if value > peak:
            peak = value
            peak_idx = i
        dd = (peak - value) / peak
        if dd > max_dd:
            max_dd = dd
            dd_start = peak_idx
            dd_end = i

    return (max_dd, dd_start, dd_end)


def generate_ma_crossover_basic() -> dict[str, Any]:
    """生成 ma_crossover_basic 黄金 case."""
    # 固定可复现输入（25 根 K 线，模拟震荡走势）
    closes = [
        100.0, 101.0, 102.0, 103.0, 99.0, 98.0, 100.0, 105.0, 107.0, 110.0,
        112.0, 108.0, 106.0, 104.0, 102.0, 100.0, 98.0, 99.0, 101.0, 103.0,
        105.0, 107.0, 109.0, 111.0, 113.0,
    ]
    fast_period = 3
    slow_period = 7
    initial_cash = 10000.0
    risk_free_rate = 0.0
    periods_per_year = 252.0

    equity = python_ma_crossover_backtest(closes, fast_period, slow_period, initial_cash)

    returns = [(equity[i + 1] - equity[i]) / equity[i] for i in range(len(equity) - 1)]
    sharpe = python_sharpe_ratio(returns, risk_free_rate, periods_per_year)
    max_dd, dd_start, dd_end = python_max_drawdown(equity)
    total_return = (equity[-1] - initial_cash) / initial_cash

    return {
        "case_id": "ma_crossover_basic",
        "description": "Simple MA crossover on 25-bar mock series; cross-language bit-equivalent check",
        "input": {
            "symbol": "GOLDEN_TEST",
            "closes": closes,
            "fast_period": fast_period,
            "slow_period": slow_period,
            "initial_cash": initial_cash,
            "risk_free_rate": risk_free_rate,
            "periods_per_year": periods_per_year,
        },
        "expected": {
            "equity_curve": equity,
            "total_return": total_return,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_dd,
            "max_drawdown_start": dd_start,
            "max_drawdown_end": dd_end,
        },
        # Tolerance per plan §7: equity_curve abs=1e-9 (cross-language float
        # summation order differs by ~2 ULP at the 12th digit; not algorithmic).
        "tolerance": {"abs": 1e-9, "rel": 0.0},
    }
