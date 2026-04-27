"""基础风控管理器.

实现：止损、止盈、最大持仓数量限制、日亏损上限检查。
同时在回测引擎和实盘引擎中使用。

数据契约（RiskConfig、RiskCheckResult）已下沉到
``quantpilot_common.contracts.risk``；本模块从那里 re-export 以保持向后兼容。
"""

from __future__ import annotations

from loguru import logger

from quantpilot_common.contracts.risk import RiskCheckResult, RiskConfig

__all__ = [
    "RiskConfig",
    "RiskCheckResult",
    "RiskManager",
]


class RiskManager:
    """实盘/回测风控管理器.

    在每次下单前调用 check_order，在每个 K 线结束时调用 check_positions。
    """

    def __init__(self, config: RiskConfig) -> None:
        self._config = config
        self._day_start_value: float | None = None
        self._trading_halted: bool = False

    def reset_daily(self, portfolio_value: float) -> None:
        """每天开始时重置日内风控状态."""
        self._day_start_value = portfolio_value
        self._trading_halted = False

    def check_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        portfolio_value: float,
        current_positions: dict[str, object],
    ) -> RiskCheckResult:
        """检查订单是否符合风控规则.

        Args:
            symbol: 标的代码
            side: 'buy' / 'sell'
            quantity: 委托数量
            price: 委托价格
            portfolio_value: 当前组合净值
            current_positions: 当前持仓字典

        Returns:
            RiskCheckResult，allowed=False 时含拒绝原因
        """
        cfg = self._config

        # 日亏损熔断
        if self._trading_halted:
            return RiskCheckResult.reject("日内亏损超限，交易已暂停")

        # 仅检查买入类订单
        if side == "buy":
            # 最大持仓数量
            if len(current_positions) >= cfg.max_position_count and symbol not in current_positions:
                return RiskCheckResult.reject(
                    f"持仓数量已达上限 {cfg.max_position_count}，拒绝开新仓"
                )

            # 单笔最大交易金额
            order_value = quantity * price
            if cfg.max_order_value and order_value > cfg.max_order_value:
                return RiskCheckResult.reject(
                    f"单笔交易金额 {order_value:.2f} 超过上限 {cfg.max_order_value:.2f}"
                )

            # 单标的最大占比
            if portfolio_value > 0 and cfg.max_single_position_pct < 1.0:
                if order_value / portfolio_value > cfg.max_single_position_pct:
                    return RiskCheckResult.reject(
                        f"单标的占比 {order_value/portfolio_value:.2%} 超过上限 "
                        f"{cfg.max_single_position_pct:.2%}"
                    )

        return RiskCheckResult.ok()

    def check_positions(
        self,
        positions: dict[str, tuple[float, float]],  # symbol -> (avg_price, current_price)
        portfolio_value: float,
    ) -> list[tuple[str, str]]:
        """检查持仓是否触发止损/止盈.

        Args:
            positions: {symbol: (avg_price, current_price)}
            portfolio_value: 当前组合净值

        Returns:
            需要平仓的 [(symbol, reason)] 列表
        """
        cfg = self._config
        actions: list[tuple[str, str]] = []

        for symbol, (avg_price, current_price) in positions.items():
            if avg_price <= 0:
                continue
            ret = (current_price - avg_price) / avg_price

            if cfg.stop_loss_pct and ret <= -cfg.stop_loss_pct:
                reason = f"止损触发: 亏损 {ret:.2%} >= {cfg.stop_loss_pct:.2%}"
                logger.warning(f"[RiskManager] {symbol} {reason}")
                actions.append((symbol, reason))

            elif cfg.take_profit_pct and ret >= cfg.take_profit_pct:
                reason = f"止盈触发: 盈利 {ret:.2%} >= {cfg.take_profit_pct:.2%}"
                logger.info(f"[RiskManager] {symbol} {reason}")
                actions.append((symbol, reason))

        # 日亏损上限检查
        if cfg.daily_loss_limit_pct and self._day_start_value:
            daily_ret = (portfolio_value - self._day_start_value) / self._day_start_value
            if daily_ret <= -cfg.daily_loss_limit_pct and not self._trading_halted:
                self._trading_halted = True
                logger.warning(
                    f"[RiskManager] 日内亏损 {daily_ret:.2%} 超过 "
                    f"{cfg.daily_loss_limit_pct:.2%}，暂停交易"
                )

        return actions

    @property
    def is_halted(self) -> bool:
        """当前是否处于熔断状态."""
        return self._trading_halted
