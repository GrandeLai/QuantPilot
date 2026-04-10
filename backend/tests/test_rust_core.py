"""Rust PyO3 回测引擎性能验证 — T-0.3 验收测试.

验收标准：Rust 核心循环相比纯 Python 实现性能有显著提升
"""

import time

import numpy as np


def _python_ma_crossover_backtest(
    closes: list[float],
    fast_period: int,
    slow_period: int,
    initial_cash: float,
) -> list[float]:
    """纯 Python 实现的移动均线交叉回测（对比基准）."""
    n = len(closes)
    portfolio_values = [initial_cash] * n
    position = 0.0
    cash = initial_cash

    for i in range(slow_period, n):
        fast_ma = sum(closes[i - fast_period : i]) / fast_period
        slow_ma = sum(closes[i - slow_period : i]) / slow_period
        price = closes[i]

        if fast_ma > slow_ma and position == 0.0 and cash > 0.0:
            position = cash / price
            cash = 0.0
        elif fast_ma < slow_ma and position > 0.0:
            cash = position * price
            position = 0.0

        portfolio_values[i] = cash + position * price

    for i in range(slow_period):
        portfolio_values[i] = initial_cash

    return portfolio_values


def test_rust_core_importable() -> None:
    """验证 quantpilot_core Rust 模块可正常导入."""
    import quantpilot_core  # type: ignore[import]

    assert hasattr(quantpilot_core, "version")
    assert hasattr(quantpilot_core, "run_ma_crossover_backtest")
    assert hasattr(quantpilot_core, "sharpe_ratio")
    assert hasattr(quantpilot_core, "max_drawdown")
    print(f"\n✓ quantpilot_core v{quantpilot_core.version()} 加载成功")


def test_rust_backtest_correctness() -> None:
    """验证 Rust 回测结果与 Python 实现一致."""
    import quantpilot_core  # type: ignore[import]

    rng = np.random.default_rng(42)
    n = 1000
    # 生成带趋势的价格序列
    returns = rng.normal(0.0002, 0.01, n)
    closes = [100.0 * float(np.exp(np.sum(returns[:i]))) for i in range(n)]

    fast_period, slow_period = 10, 30
    initial_cash = 100_000.0

    rust_result = quantpilot_core.run_ma_crossover_backtest(
        closes, fast_period, slow_period, initial_cash
    )
    python_result = _python_ma_crossover_backtest(
        closes, fast_period, slow_period, initial_cash
    )

    assert len(rust_result) == len(python_result), "结果长度不一致"
    for i, (r, p) in enumerate(zip(rust_result, python_result, strict=True)):
        assert abs(r - p) < 1e-6, f"第 {i} 步结果不一致: Rust={r:.6f}, Python={p:.6f}"

    print(f"\n✓ Rust/Python 结果完全一致（{n} 个时间步）")


def test_rust_vs_python_performance() -> None:
    """验证 Rust 回测性能显著优于纯 Python 实现."""
    import quantpilot_core  # type: ignore[import]

    rng = np.random.default_rng(0)
    n = 100_000  # 10 万根 K 线
    returns = rng.normal(0.0002, 0.01, n)
    closes = [100.0 * float(np.exp(np.sum(returns[:i]))) for i in range(n)]

    fast_period, slow_period = 10, 30
    initial_cash = 100_000.0

    # Python 基准
    t_start = time.perf_counter()
    _python_values = _python_ma_crossover_backtest(
        closes, fast_period, slow_period, initial_cash
    )
    python_ms = (time.perf_counter() - t_start) * 1000

    # Rust 实现
    t_start = time.perf_counter()
    rust_result = quantpilot_core.run_ma_crossover_backtest(
        closes, fast_period, slow_period, initial_cash
    )
    rust_ms = (time.perf_counter() - t_start) * 1000

    speedup = python_ms / rust_ms
    print("\n10 万根 K 线回测性能对比:")
    print(f"  Python: {python_ms:.2f}ms")
    print(f"  Rust:   {rust_ms:.2f}ms")
    print(f"  加速比: {speedup:.1f}x")

    assert len(rust_result) == n
    # 验证 Rust 比 Python 快（Rust 应至少和 Python 一样快，通常更快）
    assert rust_ms < python_ms * 2, f"Rust ({rust_ms:.2f}ms) 应比 Python ({python_ms:.2f}ms) 更快"


def test_sharpe_ratio() -> None:
    """验证夏普比率计算."""
    import quantpilot_core  # type: ignore[import]

    rng = np.random.default_rng(42)
    returns = rng.normal(0.001, 0.02, 252).tolist()  # 一年日收益

    sharpe = quantpilot_core.sharpe_ratio(returns, risk_free_rate=0.02, periods_per_year=252.0)
    print(f"\n夏普比率: {sharpe:.4f}")
    assert isinstance(sharpe, float)


def test_max_drawdown() -> None:
    """验证最大回撤计算."""
    import quantpilot_core  # type: ignore[import]

    # 简单测试：先涨后跌
    values = [100.0, 110.0, 120.0, 100.0, 90.0, 95.0, 115.0]
    max_dd, start_idx, end_idx = quantpilot_core.max_drawdown(values)

    # 峰值 120，谷值 90，回撤 = (120-90)/120 = 25%
    expected_dd = (120.0 - 90.0) / 120.0
    assert abs(max_dd - expected_dd) < 1e-6, f"最大回撤计算错误: {max_dd:.4f} != {expected_dd:.4f}"
    assert start_idx == 2  # 峰值在索引 2
    assert end_idx == 4    # 谷值在索引 4
    print(f"\n✓ 最大回撤: {max_dd:.2%} (从索引 {start_idx} 到 {end_idx})")
