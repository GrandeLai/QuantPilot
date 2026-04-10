"""Paper trading engine tests — T-2.1 验收."""
from __future__ import annotations

from datetime import UTC, datetime

from quantpilot.data.models import OHLCVBar
from quantpilot.paper.engine import PaperSession, PaperTradingEngine
from quantpilot.strategy.base import BaseStrategy, StrategyContext


def _bar(i: int, price: float = 100.0) -> OHLCVBar:
    return OHLCVBar(
        symbol="TEST",
        timeframe="1d",
        timestamp=datetime(2024, 1, i + 1, tzinfo=UTC),
        open=price * 0.99,
        high=price * 1.02,
        low=price * 0.97,
        close=price,
        volume=1_000_000,
    )


class AlwaysBuyStrategy(BaseStrategy):
    name = "always_buy"
    description = "Buys every bar once"

    def on_bar(self, bar: OHLCVBar, context: StrategyContext) -> None:
        if not context.positions:
            context.buy(bar.symbol, 100, bar.close)


class TestPaperSession:
    def test_initial_state(self) -> None:
        sess = PaperSession(symbol="TEST", timeframe="1d", initial_cash=100_000.0)
        assert sess.cash == 100_000.0
        assert sess.positions == {}
        assert sess.trades == []

    def test_portfolio_value_no_positions(self) -> None:
        sess = PaperSession(symbol="TEST", timeframe="1d", initial_cash=50_000.0)
        assert sess.portfolio_value({}) == 50_000.0


class TestPaperTradingEngine:
    def test_process_bar_updates_session(self) -> None:
        sess = PaperSession(symbol="TEST", timeframe="1d", initial_cash=100_000.0)
        engine = PaperTradingEngine(sess, commission_rate=0.001, slippage_pct=0.0005)
        strategy = AlwaysBuyStrategy()
        strategy.on_init(engine._context)

        bar = _bar(0, 100.0)
        engine.process_bar(strategy, bar)

        assert "TEST" in sess.positions
        assert sess.positions["TEST"].quantity == 100
        assert sess.cash < 100_000.0

    def test_process_multiple_bars(self) -> None:
        sess = PaperSession(symbol="TEST", timeframe="1d", initial_cash=100_000.0)
        engine = PaperTradingEngine(sess, commission_rate=0.001, slippage_pct=0.0005)
        strategy = AlwaysBuyStrategy()
        strategy.on_init(engine._context)

        bars = [_bar(i, 100.0 + i) for i in range(5)]
        for bar in bars:
            engine.process_bar(strategy, bar)

        assert sess.portfolio_value({"TEST": bars[-1].close}) > 0

    def test_portfolio_value_with_position(self) -> None:
        sess = PaperSession(symbol="TEST", timeframe="1d", initial_cash=100_000.0)
        engine = PaperTradingEngine(sess, commission_rate=0.001, slippage_pct=0.0005)
        strategy = AlwaysBuyStrategy()
        strategy.on_init(engine._context)

        bar = _bar(0, 100.0)
        engine.process_bar(strategy, bar)

        pv = sess.portfolio_value({"TEST": 120.0})
        assert pv > 100_000.0
