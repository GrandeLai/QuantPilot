"""回测绩效报告 golden case.

实现与 Rust ``src/reports.rs::calculate_report``
**逐行对齐**的独立 Python 参考实现。
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from quantpilot_golden.cases.ma_crossover import python_ma_crossover_backtest


def python_calculate_report(
    equity_curve: list[float],
    initial_cash: float,
    risk_free_rate: float = 0.0,
    periods_per_year: float = 252.0,
) -> dict[str, Any]:
    """与 Rust calculate_report 逐行对齐的参考实现."""
    n = len(equity_curve)
    total_bars = n

    if n < 2 or initial_cash <= 0.0:
        return {
            "total_return": 0.0, "annual_return": 0.0,
            "max_drawdown": 0.0, "max_drawdown_start": 0, "max_drawdown_end": 0,
            "volatility": 0.0, "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0, "calmar_ratio": 0.0, "total_bars": total_bars,
        }

    # ── 日收益率 ──────────────────────────────────────────────────────────────
    returns = [
        (equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]
        for i in range(1, n)
    ]

    # ── 总收益 & CAGR ──────────────────────────────────────────────────────────
    total_return = (equity_curve[-1] - initial_cash) / initial_cash
    years = (n - 1) / periods_per_year  # n-1: same as Rust
    annual_return = (1.0 + total_return) ** (1.0 / years) - 1.0 if years > 0 else 0.0

    # ── 波动率（年化） ─────────────────────────────────────────────────────────
    m = len(returns)
    mean_ret = sum(returns) / m
    variance = sum((r - mean_ret) ** 2 for r in returns) / (m - 1)
    std_dev = math.sqrt(variance)
    volatility = std_dev * math.sqrt(periods_per_year)

    # ── Sharpe ────────────────────────────────────────────────────────────────
    daily_rf = risk_free_rate / periods_per_year
    if std_dev == 0.0:
        sharpe = 0.0
    else:
        sharpe = (mean_ret - daily_rf) / std_dev * math.sqrt(periods_per_year)

    # ── Sortino ───────────────────────────────────────────────────────────────
    downside_returns = [r for r in returns if r < daily_rf]
    if downside_returns:
        down_sq_sum = sum((r - daily_rf) ** 2 for r in downside_returns)
        downside_std = math.sqrt(down_sq_sum / len(downside_returns))
        sortino = (mean_ret - daily_rf) / downside_std * math.sqrt(periods_per_year) \
            if downside_std > 0 else 0.0
    else:
        sortino = float("inf")

    # ── Max Drawdown ──────────────────────────────────────────────────────────
    max_dd = 0.0
    peak = equity_curve[0]
    peak_idx = 0
    dd_start = 0
    dd_end = 0
    for i in range(1, n):
        v = equity_curve[i]
        if v > peak:
            peak = v
            peak_idx = i
        dd = (peak - v) / peak
        if dd > max_dd:
            max_dd = dd
            dd_start = peak_idx
            dd_end = i

    # ── Calmar ────────────────────────────────────────────────────────────────
    calmar = annual_return / max_dd if max_dd > 0.0 else 0.0

    return {
        "total_return": total_return,
        "annual_return": annual_return,
        "max_drawdown": max_dd,
        "max_drawdown_start": dd_start,
        "max_drawdown_end": dd_end,
        "volatility": volatility,
        "sharpe_ratio": sharpe,
        "sortino_ratio": sortino if math.isfinite(sortino) else None,
        "calmar_ratio": calmar,
        "total_bars": total_bars,
    }


FIXTURE_CLOSES: list[float] = [
    100.0, 101.0, 102.0, 103.0,  99.0,  98.0, 100.0, 105.0, 107.0, 110.0,
    112.0, 108.0, 106.0, 104.0, 102.0, 100.0,  98.0,  99.0, 101.0, 103.0,
    105.0, 107.0, 109.0, 111.0, 113.0,
]


def generate_reports_basic() -> dict[str, Any]:
    """生成 reports_basic golden case."""
    closes = FIXTURE_CLOSES
    initial_cash = 10_000.0
    fast, slow = 3, 7
    equity_curve = python_ma_crossover_backtest(closes, fast, slow, initial_cash)

    report = python_calculate_report(
        equity_curve=equity_curve,
        initial_cash=initial_cash,
        risk_free_rate=0.0,
        periods_per_year=252.0,
    )

    return {
        "case_id": "reports_basic",
        "description": (
            "Full metrics report for MA crossover on 25-bar mock series; "
            "cross-language equivalence check"
        ),
        "input": {
            "closes": closes,
            "fast_period": fast,
            "slow_period": slow,
            "initial_cash": initial_cash,
            "risk_free_rate": 0.0,
            "periods_per_year": 252.0,
        },
        "expected": report,
        "tolerance": {
            "abs": 1e-9,
            "rel": 1e-9,
            "note": "各指标容差 1e-9；sortino=null 表示无下行收益时的 inf",
        },
    }


def main() -> None:
    """生成并写出 reports_basic.json."""
    data = generate_reports_basic()
    out_path = (
        Path(__file__).parents[5]
        / "common"
        / "data-store"
        / "golden"
        / "expected"
        / "reports_basic.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Written: {out_path}")

    r = data["expected"]
    print(f"\nReport: total_return={r['total_return']:.4f} sharpe={r['sharpe_ratio']:.4f} "
          f"max_dd={r['max_drawdown']:.4f} calmar={r['calmar_ratio']:.4f}")


if __name__ == "__main__":
    main()
