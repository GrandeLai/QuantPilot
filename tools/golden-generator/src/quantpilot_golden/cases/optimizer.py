"""策略参数网格搜索 golden case.

实现与 Rust ``src/optimizer.rs::grid_search_ma_crossover``
和 Python ``quantpilot_quant.optimize.engine.OptimizationEngine.grid_search``
**逐行对齐**的独立参考实现。

使用已有的 ma_crossover.py 中的纯 Python 工具函数。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quantpilot_golden.cases.ma_crossover import (
    python_ma_crossover_backtest,
    python_max_drawdown,
    python_sharpe_ratio,
)

FIXTURE_CLOSES: list[float] = [
    100.0, 101.0, 102.0, 103.0,  99.0,  98.0, 100.0, 105.0, 107.0, 110.0,
    112.0, 108.0, 106.0, 104.0, 102.0, 100.0,  98.0,  99.0, 101.0, 103.0,
    105.0, 107.0, 109.0, 111.0, 113.0,
]


def python_grid_search_ma_crossover(
    closes: list[float],
    initial_cash: float,
    fast_periods: list[int],
    slow_periods: list[int],
    risk_free_rate: float = 0.0,
    periods_per_year: float = 252.0,
) -> list[dict[str, Any]]:
    """与 Rust grid_search_ma_crossover 逐行对齐的参考实现.

    跳过 fast >= slow 的组合。结果按 Sharpe 降序排列。
    """
    results = []

    for fast in fast_periods:
        for slow in slow_periods:
            if fast >= slow:
                continue

            try:
                equity = python_ma_crossover_backtest(closes, fast, slow, initial_cash)
            except ValueError:
                continue

            n = len(equity)
            if n < 2:
                continue

            # 日收益率（与 Rust 对齐：returns = diff / equity[:-1]）
            returns = [
                (equity[i] - equity[i - 1]) / equity[i - 1]
                for i in range(1, n)
            ]

            sharpe = python_sharpe_ratio(returns, risk_free_rate, periods_per_year)
            dd, dd_start, dd_end = python_max_drawdown(equity)
            total_return = (equity[-1] - initial_cash) / initial_cash if initial_cash > 0 else 0.0

            results.append({
                "fast_period": fast,
                "slow_period": slow,
                "sharpe_ratio": sharpe,
                "total_return": total_return,
                "max_drawdown": dd,
            })

    # 按 Sharpe 降序（与 Python OptimizationEngine.grid_search 一致）
    results.sort(key=lambda r: r["sharpe_ratio"], reverse=True)
    return results


def generate_optimizer_grid_basic() -> dict[str, Any]:
    """生成 optimizer_grid_basic golden case."""
    closes = FIXTURE_CLOSES
    fast_periods = [2, 3, 5]
    slow_periods = [5, 7, 10]
    initial_cash = 10_000.0

    results = python_grid_search_ma_crossover(
        closes=closes,
        initial_cash=initial_cash,
        fast_periods=fast_periods,
        slow_periods=slow_periods,
        risk_free_rate=0.0,
        periods_per_year=252.0,
    )

    return {
        "case_id": "optimizer_grid_basic",
        "description": (
            "MA crossover grid search on 25-bar mock series; "
            "cross-language equivalence check"
        ),
        "input": {
            "closes": closes,
            "initial_cash": initial_cash,
            "fast_periods": fast_periods,
            "slow_periods": slow_periods,
            "risk_free_rate": 0.0,
            "periods_per_year": 252.0,
        },
        "expected": results,
        "tolerance": {
            "abs": 1e-9,
            "rel": 1e-9,
            "note": "回测 equity_curve 用 1e-9 容差；Sharpe/metrics 也在 1e-9 内",
        },
    }


def main() -> None:
    """生成并写出 optimizer_grid_basic.json."""
    data = generate_optimizer_grid_basic()
    out_path = (
        Path(__file__).parents[5]  # repo root: QuantPilot/
        / "common"
        / "data-store"
        / "golden"
        / "expected"
        / "optimizer_grid_basic.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Written: {out_path}")

    print(f"\nTop 3 results:")
    for r in data["expected"][:3]:
        print(f"  fast={r['fast_period']}, slow={r['slow_period']}: sharpe={r['sharpe_ratio']:.4f}")


if __name__ == "__main__":
    main()
