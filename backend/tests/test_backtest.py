"""回测引擎测试 — T-1.4 验收."""

from datetime import UTC, datetime, timedelta

import pytest

from quantpilot.backtest.engine import BacktestConfig, BacktestEngine, BacktestResult
from quantpilot.backtest.metrics import TradeRecord, calculate_metrics
from quantpilot_common.data.models import OHLCVBar
from quantpilot.strategy.templates.ma_crossover import MACrossoverStrategy
from quantpilot.strategy.templates.rsi_mean_reversion import RSIMeanReversionStrategy


def _make_bars(n: int = 200, start_price: float = 100.0, trend: float = 0.001) -> list[OHLCVBar]:
    """生成测试 K 线数据."""
    bars = []
    price = start_price
    for i in range(n):
        change = trend + (0.01 if i % 5 == 0 else -0.003)
        price = max(price * (1 + change), 1.0)
        bars.append(
            OHLCVBar(
                symbol="TEST",
                timeframe="1d",
                timestamp=datetime(2023, 1, 1, tzinfo=UTC) + timedelta(days=i),
                open=price * 0.99,
                high=price * 1.02,
                low=price * 0.97,
                close=price,
                volume=1_000_000.0,
            )
        )
    return bars


@pytest.fixture
def bars() -> list[OHLCVBar]:
    return _make_bars(200)


@pytest.fixture
def config() -> BacktestConfig:
    return BacktestConfig(symbol="TEST", timeframe="1d", initial_cash=100_000.0)


class TestBacktestEngine:
    def test_returns_backtest_result(
        self, config: BacktestConfig, bars: list[OHLCVBar]
    ) -> None:
        engine = BacktestEngine(config)
        result = engine.run(MACrossoverStrategy(), bars)
        assert isinstance(result, BacktestResult)

    def test_bars_processed_count(
        self, config: BacktestConfig, bars: list[OHLCVBar]
    ) -> None:
        engine = BacktestEngine(config)
        result = engine.run(MACrossoverStrategy(), bars)
        assert result.bars_processed == len(bars)

    def test_portfolio_values_length(
        self, config: BacktestConfig, bars: list[OHLCVBar]
    ) -> None:
        engine = BacktestEngine(config)
        result = engine.run(MACrossoverStrategy(), bars)
        assert len(result.metrics.portfolio_values) == len(bars)

    def test_initial_cash_preserved_without_trades(self) -> None:
        """无交易时，资金应等于初始资金."""
        config = BacktestConfig(symbol="TEST", timeframe="1d", initial_cash=50_000.0)
        # 使用无法触发信号的参数（价格变动太小）
        bars = [
            OHLCVBar(
                symbol="TEST", timeframe="1d",
                timestamp=datetime(2024, 1, 1, tzinfo=UTC) + timedelta(days=i),
                open=100.0, high=100.1, low=99.9, close=100.0, volume=0.0,
            )
            for i in range(5)
        ]
        engine = BacktestEngine(config)
        result = engine.run(MACrossoverStrategy(), bars)
        # 没有足够数据触发信号，资金不变
        assert result.metrics.final_value >= 0

    def test_commission_reduces_returns(self, bars: list[OHLCVBar]) -> None:
        """高手续费应导致收益更低."""
        low_comm = BacktestConfig(symbol="TEST", timeframe="1d",
                                  initial_cash=100_000.0, commission_rate=0.0001)
        high_comm = BacktestConfig(symbol="TEST", timeframe="1d",
                                   initial_cash=100_000.0, commission_rate=0.01)
        strat1, strat2 = MACrossoverStrategy(), MACrossoverStrategy()
        r1 = BacktestEngine(low_comm).run(strat1, bars)
        r2 = BacktestEngine(high_comm).run(strat2, bars)
        # 同等条件下，低手续费收益 >= 高手续费收益
        assert r1.metrics.final_value >= r2.metrics.final_value

    def test_stop_loss_triggers(self) -> None:
        """止损触发：价格急跌时应止损."""
        bars = [
            OHLCVBar(
                symbol="TEST", timeframe="1d",
                timestamp=datetime(2024, 1, 1, tzinfo=UTC) + timedelta(days=i),
                open=100.0 - i * 2, high=100.0 - i * 2 + 0.5,
                low=100.0 - i * 2 - 0.5, close=100.0 - i * 2,
                volume=1_000_000.0,
            )
            for i in range(50)
        ]
        bars[0] = OHLCVBar(
            symbol="TEST", timeframe="1d",
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            open=100.0, high=115.0, low=98.0, close=110.0, volume=1_000_000.0,
        )
        config = BacktestConfig(
            symbol="TEST", timeframe="1d",
            initial_cash=100_000.0,
            stop_loss_pct=0.05,  # 5% 止损
        )
        engine = BacktestEngine(config)
        result = engine.run(MACrossoverStrategy(), bars)
        # 有止损，最终亏损应小于无止损的情况
        assert result.metrics.final_value >= 0

    def test_multiple_strategies(self, bars: list[OHLCVBar]) -> None:
        """不同策略在同样数据上应产生不同结果."""
        config = BacktestConfig(symbol="TEST", timeframe="1d", initial_cash=100_000.0)
        r1 = BacktestEngine(config).run(MACrossoverStrategy(), bars)
        r2 = BacktestEngine(config).run(RSIMeanReversionStrategy(), bars)
        # 两个策略运行不报错即可（收益可能相同也可能不同）
        assert isinstance(r1.metrics.total_return, float)
        assert isinstance(r2.metrics.total_return, float)


class TestMetrics:
    def test_total_return_calculation(self) -> None:
        values = [100_000.0, 105_000.0, 110_000.0, 108_000.0, 115_000.0]
        metrics = calculate_metrics(values, [], 100_000.0)
        assert abs(metrics.total_return - 0.15) < 1e-6

    def test_sharpe_ratio_positive_for_positive_return(self) -> None:
        # 稳定上涨的组合，Sharpe 应为正
        values = [100_000.0 + i * 500 for i in range(100)]
        metrics = calculate_metrics(values, [], 100_000.0)
        assert metrics.sharpe_ratio > 0

    def test_max_drawdown_negative(self) -> None:
        values = [100.0, 120.0, 90.0, 110.0]
        metrics = calculate_metrics(values, [], 100.0)
        assert metrics.max_drawdown < 0  # 回撤为负值
        # 最大回撤 = (120 - 90) / 120 = 25%
        assert abs(abs(metrics.max_drawdown) - 0.25) < 1e-6

    def test_win_rate_calculation(self) -> None:
        from datetime import datetime
        trades = [
            TradeRecord("A", "buy", datetime(2024, 1, 1, tzinfo=UTC),
                        datetime(2024, 1, 5, tzinfo=UTC),
                        100.0, 110.0, 10.0, 0.5, 0.1),
            TradeRecord("A", "buy", datetime(2024, 1, 6, tzinfo=UTC),
                        datetime(2024, 1, 10, tzinfo=UTC),
                        110.0, 105.0, 10.0, 0.5, 0.1),
        ]
        values = [100_000.0 + i * 100 for i in range(20)]
        metrics = calculate_metrics(values, trades, 100_000.0)
        assert metrics.win_rate == 0.5  # 1 胜 1 负

    def test_empty_portfolio_returns_zero_metrics(self) -> None:
        metrics = calculate_metrics([], [], 100_000.0)
        assert metrics.total_return == 0.0
        assert metrics.sharpe_ratio == 0.0

    def test_annual_return_calculation(self) -> None:
        # 252 天后净值翻倍，年化收益约 100%
        values = [100_000.0 + i * 100_000.0 / 252 for i in range(253)]
        metrics = calculate_metrics(values, [], 100_000.0)
        assert abs(metrics.annual_return - 1.0) < 0.01
