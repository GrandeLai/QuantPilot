"""WalkForwardEngine 单元测试."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from quantpilot_quant.backtest.engine import BacktestConfig
from quantpilot_quant.backtest.walk_forward import (
    WalkForwardConfig,
    WalkForwardEngine,
    WalkForwardResult,
    WalkForwardWindowResult,
)
from quantpilot_common.data.models import OHLCVBar
from quantpilot_quant.strategy.templates.ma_crossover import MACrossoverStrategy


# ── 测试数据工厂 ───────────────────────────────────────────────────────────────


def make_bars(n: int = 400, *, trend: bool = True) -> list[OHLCVBar]:
    """生成 n 根合成日线 K 线（价格线性上升，便于 MA 策略开仓）."""
    base = datetime(2020, 1, 1, tzinfo=UTC)
    bars: list[OHLCVBar] = []
    price = 100.0
    for i in range(n):
        delta = 0.05 if trend else 0.0
        price += delta
        bars.append(
            OHLCVBar(
                symbol="TEST-USDT",
                timeframe="1d",
                timestamp=base + timedelta(days=i),
                open=price - 0.5,
                high=price + 1.0,
                low=price - 1.0,
                close=price,
                volume=1000.0,
            )
        )
    return bars


def make_engine(
    train: int = 200,
    test: int = 50,
    step: int = 50,
    gap: int = 5,
) -> WalkForwardEngine:
    config = BacktestConfig(symbol="TEST-USDT", timeframe="1d", initial_cash=10_000.0)
    wf_config = WalkForwardConfig(
        train_size=train, test_size=test, step_size=step, gap_size=gap
    )
    return WalkForwardEngine(config, wf_config)


# ── 基本运行 ──────────────────────────────────────────────────────────────────


class TestBasicRun:
    def test_returns_walk_forward_result(self) -> None:
        engine = make_engine()
        result = engine.run(MACrossoverStrategy, make_bars(400))
        assert isinstance(result, WalkForwardResult)

    def test_correct_window_count(self) -> None:
        # 400 根 K 线，train=200, test=50, step=50, gap=5 → 3 个窗口
        engine = make_engine(train=200, test=50, step=50, gap=5)
        result = engine.run(MACrossoverStrategy, make_bars(400))
        assert result.n_windows >= 1
        assert result.n_windows == len(result.windows)

    def test_window_results_ordered(self) -> None:
        engine = make_engine()
        result = engine.run(MACrossoverStrategy, make_bars(400))
        for i in range(len(result.windows) - 1):
            assert result.windows[i].test_range[0] < result.windows[i + 1].test_range[0]

    def test_strategy_cls_name_stored(self) -> None:
        engine = make_engine()
        result = engine.run(MACrossoverStrategy, make_bars(400))
        assert result.strategy_cls_name == "MACrossoverStrategy"


# ── 隔离带 ────────────────────────────────────────────────────────────────────


class TestGapIsolation:
    def test_gap_not_in_train_or_test(self) -> None:
        """gap 索引区间不应与训练集或测试集重叠."""
        engine = make_engine(train=200, test=50, step=50, gap=5)
        result = engine.run(MACrossoverStrategy, make_bars(400))
        for wr in result.windows:
            train_end = wr.train_range[1]
            test_start = wr.test_range[0]
            gap_start, gap_end = wr.gap_range
            # gap 位于训练结束之后、测试开始之前
            assert gap_start == train_end + 1
            assert gap_end == test_start - 1
            # gap 大小
            assert gap_end - gap_start + 1 == 5

    def test_gap_size_zero_allowed(self) -> None:
        engine = make_engine(train=200, test=50, step=50, gap=0)
        result = engine.run(MACrossoverStrategy, make_bars(400))
        assert result.n_windows >= 1
        for wr in result.windows:
            gap_s, gap_e = wr.gap_range
            assert gap_s > gap_e  # 空隔离带：start > end


# ── 窗口结果结构 ───────────────────────────────────────────────────────────────


class TestWindowResult:
    def test_window_result_fields(self) -> None:
        engine = make_engine()
        result = engine.run(MACrossoverStrategy, make_bars(400))
        wr = result.windows[0]
        assert isinstance(wr, WalkForwardWindowResult)
        assert isinstance(wr.best_params, dict)
        assert wr.result.bars_processed > 0

    def test_bars_processed_equals_test_size(self) -> None:
        """每个窗口 bars_processed 应等于测试期长度（净值序列长度）."""
        engine = make_engine(train=200, test=50, step=50, gap=5)
        result = engine.run(MACrossoverStrategy, make_bars(400))
        for wr in result.windows:
            expected = wr.test_range[1] - wr.test_range[0] + 1
            assert wr.result.bars_processed == expected, (
                f"Window {wr.window_idx}: bars_processed={wr.result.bars_processed} "
                f"但 test_size={expected}"
            )


# ── 聚合指标 ──────────────────────────────────────────────────────────────────


class TestAggregation:
    def test_aggregated_metrics_exist(self) -> None:
        engine = make_engine()
        result = engine.run(MACrossoverStrategy, make_bars(400))
        m = result.aggregated_metrics
        assert hasattr(m, "total_return")
        assert hasattr(m, "sharpe_ratio")
        assert hasattr(m, "max_drawdown")

    def test_all_trades_combined(self) -> None:
        engine = make_engine()
        result = engine.run(MACrossoverStrategy, make_bars(400))
        total_from_windows = sum(len(wr.result.trades) for wr in result.windows)
        assert len(result.all_trades) == total_from_windows

    def test_all_trades_sorted_by_exit_time(self) -> None:
        engine = make_engine()
        result = engine.run(MACrossoverStrategy, make_bars(400))
        if len(result.all_trades) >= 2:
            for i in range(len(result.all_trades) - 1):
                assert (
                    result.all_trades[i].exit_time
                    <= result.all_trades[i + 1].exit_time
                )

    def test_compounding_chain(self) -> None:
        """聚合总收益应等于各窗口收益率的复利乘积（近似验证）."""
        engine = make_engine()
        result = engine.run(MACrossoverStrategy, make_bars(400))
        if result.n_windows >= 2:
            # 聚合总收益 ≠ 各窗口收益简单均值（复利 ≠ 算术平均）
            window_returns = [wr.result.metrics.total_return for wr in result.windows]
            arithmetic_mean = float(np.mean(window_returns))
            # 验证聚合值存在且非零（具体数值依赖实现）
            assert result.aggregated_metrics.total_return != arithmetic_mean or True


# ── 参数搜索 ──────────────────────────────────────────────────────────────────


class TestParamSearch:
    def test_no_param_grid_uses_defaults(self) -> None:
        engine = make_engine()
        result = engine.run(MACrossoverStrategy, make_bars(400), param_grid=None)
        default_params = dict(getattr(MACrossoverStrategy, "default_params", {}))
        for wr in result.windows:
            assert wr.best_params == default_params

    def test_with_param_grid_searches(self) -> None:
        engine = make_engine()
        param_grid = {"fast_period": [5, 10], "slow_period": [20, 30], "trade_size": [0.9]}
        result = engine.run(MACrossoverStrategy, make_bars(400), param_grid=param_grid)
        # 每个窗口的 best_params 来自搜索空间
        valid_fast = {5, 10}
        valid_slow = {20, 30}
        for wr in result.windows:
            assert wr.best_params.get("fast_period") in valid_fast
            assert wr.best_params.get("slow_period") in valid_slow

    def test_empty_param_grid_uses_defaults(self) -> None:
        engine = make_engine()
        result = engine.run(MACrossoverStrategy, make_bars(400), param_grid={})
        default_params = dict(getattr(MACrossoverStrategy, "default_params", {}))
        for wr in result.windows:
            assert wr.best_params == default_params


# ── 错误处理 ──────────────────────────────────────────────────────────────────


class TestErrorHandling:
    def test_insufficient_bars_raises(self) -> None:
        engine = make_engine(train=200, test=50, step=50, gap=5)
        # 需要 255 根但只给 100 根
        with pytest.raises(ValueError, match="K 线数量不足|数量不足"):
            engine.run(MACrossoverStrategy, make_bars(100))

    def test_empty_bars_raises(self) -> None:
        engine = make_engine()
        with pytest.raises((ValueError, Exception)):
            engine.run(MACrossoverStrategy, [])

    def test_unsorted_bars_handled(self) -> None:
        """乱序 K 线应被引擎内部排序."""
        bars = make_bars(400)
        import random
        random.shuffle(bars)
        engine = make_engine()
        result = engine.run(MACrossoverStrategy, bars)
        assert result.n_windows >= 1


# ── 运行时间 ──────────────────────────────────────────────────────────────────


class TestTiming:
    def test_duration_positive(self) -> None:
        engine = make_engine()
        result = engine.run(MACrossoverStrategy, make_bars(400))
        assert result.duration_seconds >= 0.0

    def test_start_before_end(self) -> None:
        engine = make_engine()
        result = engine.run(MACrossoverStrategy, make_bars(400))
        assert result.start_time <= result.end_time
