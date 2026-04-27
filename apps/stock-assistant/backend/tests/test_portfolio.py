"""多策略组合管理测试 — T-3.6 验收."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantpilot_common.data.models import OHLCVBar
from quantpilot_stock.paper.engine import PaperSession
from quantpilot_stock.portfolio.manager import PortfolioManager, StrategySlot
from quantpilot_common.contracts import BaseStrategy, StrategyContext


def _bar(i: int, price: float = 100.0) -> OHLCVBar:
    return OHLCVBar(
        symbol="TEST",
        timeframe="1d",
        timestamp=datetime(2024, 1, i + 1, tzinfo=UTC),
        open=price * 0.99,
        high=price * 1.01,
        low=price * 0.98,
        close=price,
        volume=1_000_000,
    )


class BuyOnceStrategy(BaseStrategy):
    name = "buy_once"
    description = "Buy on first bar"

    def on_bar(self, bar: OHLCVBar, context: StrategyContext) -> None:
        if not context.positions:
            context.buy(bar.symbol, 10, bar.close)


class TestStrategySlot:
    def test_slot_initial_state(self) -> None:
        sess = PaperSession(symbol="TEST", timeframe="1d", initial_cash=50_000.0)
        slot = StrategySlot(name="s1", session=sess, allocation=50_000.0)
        assert slot.name == "s1"
        assert slot.allocation == 50_000.0


class TestPortfolioManager:
    def test_add_strategy(self) -> None:
        pm = PortfolioManager(total_cash=100_000.0)
        pm.add_strategy("strat1", BuyOnceStrategy(), "TEST", "1d", allocation=50_000.0)
        assert "strat1" in pm.strategies

    def test_add_strategy_exceeds_cash_raises(self) -> None:
        pm = PortfolioManager(total_cash=100_000.0)
        pm.add_strategy("s1", BuyOnceStrategy(), "TEST", "1d", allocation=60_000.0)
        with pytest.raises(ValueError, match="资金不足"):
            pm.add_strategy("s2", BuyOnceStrategy(), "TEST", "1d", allocation=60_000.0)

    def test_process_bar_all_strategies(self) -> None:
        pm = PortfolioManager(total_cash=100_000.0)
        pm.add_strategy("s1", BuyOnceStrategy(), "TEST", "1d", allocation=50_000.0)
        pm.add_strategy("s2", BuyOnceStrategy(), "TEST2", "1d", allocation=50_000.0)
        bar1 = _bar(0, 100.0)
        bar2 = OHLCVBar(
            symbol="TEST2",
            timeframe="1d",
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            open=200.0,
            high=202.0,
            low=198.0,
            close=200.0,
            volume=500_000,
        )
        pm.process_bar("s1", bar1)
        pm.process_bar("s2", bar2)
        summary = pm.summary({"TEST": 100.0, "TEST2": 200.0})
        assert summary["total_portfolio_value"] > 0
        assert len(summary["strategies"]) == 2

    def test_remove_strategy(self) -> None:
        pm = PortfolioManager(total_cash=100_000.0)
        pm.add_strategy("s1", BuyOnceStrategy(), "TEST", "1d", allocation=50_000.0)
        pm.remove_strategy("s1")
        assert "s1" not in pm.strategies

    def test_correlation_matrix_two_strategies(self) -> None:
        pm = PortfolioManager(total_cash=200_000.0)
        pm.add_strategy("s1", BuyOnceStrategy(), "TEST", "1d", allocation=100_000.0)
        pm.add_strategy("s2", BuyOnceStrategy(), "TEST2", "1d", allocation=100_000.0)
        # Process several bars to build portfolio history
        for i in range(10):
            bar = _bar(i, 100.0 + i)
            bar2 = OHLCVBar(
                symbol="TEST2",
                timeframe="1d",
                timestamp=datetime(2024, 1, i + 1, tzinfo=UTC),
                open=200.0,
                high=202.0,
                low=198.0,
                close=200.0 + i,
                volume=500_000,
            )
            pm.process_bar("s1", bar)
            pm.process_bar("s2", bar2)
        corr = pm.correlation_matrix()
        assert "s1" in corr
        assert "s2" in corr
