"""风控管理器测试 — T-1.5 验收."""

import pytest

from quantpilot.risk.manager import RiskCheckResult, RiskConfig, RiskManager


@pytest.fixture
def default_config() -> RiskConfig:
    return RiskConfig(
        stop_loss_pct=0.05,
        take_profit_pct=0.15,
        max_position_count=5,
        max_single_position_pct=0.30,
        daily_loss_limit_pct=0.05,
    )


@pytest.fixture
def manager(default_config: RiskConfig) -> RiskManager:
    m = RiskManager(default_config)
    m.reset_daily(100_000.0)
    return m


class TestOrderCheck:
    def test_normal_buy_allowed(self, manager: RiskManager) -> None:
        result = manager.check_order(
            symbol="AAPL", side="buy",
            quantity=100, price=100.0,
            portfolio_value=100_000.0,
            current_positions={},
        )
        assert result.allowed

    def test_too_many_positions_rejected(self, manager: RiskManager) -> None:
        existing = {f"STOCK{i}": None for i in range(5)}
        result = manager.check_order(
            "NEW", "buy", 100, 100.0, 100_000.0, existing
        )
        assert not result.allowed
        assert "持仓数量" in result.reason

    def test_single_position_pct_exceeded(self, manager: RiskManager) -> None:
        # 买 400 股 * 100 = 40000，超过组合 30% (= 30000)
        result = manager.check_order(
            "AAPL", "buy", 400, 100.0, 100_000.0, {}
        )
        assert not result.allowed
        assert "占比" in result.reason

    def test_sell_always_allowed(self, manager: RiskManager) -> None:
        result = manager.check_order(
            "AAPL", "sell", 100, 100.0, 100_000.0, {"AAPL": None}
        )
        assert result.allowed

    def test_halted_trading_rejected(self, manager: RiskManager) -> None:
        manager._trading_halted = True
        result = manager.check_order("AAPL", "buy", 100, 100.0, 100_000.0, {})
        assert not result.allowed
        assert "暂停" in result.reason

    def test_max_order_value(self) -> None:
        config = RiskConfig(max_order_value=5_000.0)
        m = RiskManager(config)
        m.reset_daily(100_000.0)
        result = m.check_order("AAPL", "buy", 100, 100.0, 100_000.0, {})
        assert not result.allowed  # 100 * 100 = 10000 > 5000


class TestPositionCheck:
    def test_stop_loss_triggered(self, manager: RiskManager) -> None:
        positions = {"AAPL": (100.0, 93.0)}  # 亏损 7% > 止损 5%
        actions = manager.check_positions(positions, 100_000.0)
        assert any(sym == "AAPL" for sym, _ in actions)

    def test_take_profit_triggered(self, manager: RiskManager) -> None:
        positions = {"AAPL": (100.0, 120.0)}  # 盈利 20% > 止盈 15%
        actions = manager.check_positions(positions, 100_000.0)
        assert any(sym == "AAPL" for sym, _ in actions)

    def test_normal_position_no_action(self, manager: RiskManager) -> None:
        positions = {"AAPL": (100.0, 103.0)}  # 盈利 3%，不触发
        actions = manager.check_positions(positions, 100_000.0)
        assert len(actions) == 0

    def test_daily_loss_limit_halts_trading(self) -> None:
        config = RiskConfig(daily_loss_limit_pct=0.05)
        m = RiskManager(config)
        m.reset_daily(100_000.0)
        # 亏损 6% 触发熔断
        m.check_positions({}, 94_000.0)
        assert m.is_halted

    def test_reset_daily_clears_halt(self, manager: RiskManager) -> None:
        manager._trading_halted = True
        manager.reset_daily(100_000.0)
        assert not manager.is_halted


class TestRiskCheckResult:
    def test_ok(self) -> None:
        r = RiskCheckResult.ok()
        assert r.allowed
        assert r.reason == ""

    def test_reject(self) -> None:
        r = RiskCheckResult.reject("持仓超限")
        assert not r.allowed
        assert r.reason == "持仓超限"
