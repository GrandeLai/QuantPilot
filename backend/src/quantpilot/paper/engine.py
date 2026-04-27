"""模拟盘交易引擎 — PaperSession & PaperTradingEngine.

提供本地模拟撮合：
  - PaperSession   会话状态（资金、持仓、交易记录、净值历史）
  - PaperTradingEngine  驱动策略逐 bar 运行并执行撮合
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from quantpilot.backtest.metrics import TradeRecord
from quantpilot.strategy.base import Order, OrderSide, Position, StrategyContext

if TYPE_CHECKING:
    from quantpilot_common.data.models import OHLCVBar
    from quantpilot.strategy.base import BaseStrategy


@dataclass
class PaperSession:
    """模拟盘会话状态.

    Args:
        symbol: 交易标的
        timeframe: K 线周期
        initial_cash: 初始资金，默认 1,000,000
    """

    symbol: str
    timeframe: str
    initial_cash: float = 1_000_000.0

    # 运行时状态（post_init 初始化）
    cash: float = field(init=False)
    positions: dict[str, Position] = field(init=False, default_factory=dict)
    trades: list[TradeRecord] = field(init=False, default_factory=list)
    portfolio_history: list[float] = field(init=False, default_factory=list)
    started_at: datetime = field(init=False)
    last_bar_at: datetime | None = field(init=False, default=None)
    bars_processed: int = field(init=False, default=0)
    is_running: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        self.cash = self.initial_cash
        self.started_at = datetime.now(tz=UTC)

    def portfolio_value(self, current_prices: dict[str, float]) -> float:
        """计算当前组合总价值.

        Args:
            current_prices: 各标的最新价格映射

        Returns:
            现金 + 持仓市值
        """
        equity = sum(
            pos.quantity * current_prices.get(pos.symbol, pos.avg_price)
            for pos in self.positions.values()
        )
        return self.cash + equity


class PaperTradingEngine:
    """模拟盘撮合引擎.

    将策略与 PaperSession 绑定，逐 bar 驱动执行。

    Args:
        session: 模拟盘会话对象
        commission_rate: 手续费率，默认 0.1%
        slippage_pct: 滑点比例，默认 0.05%
        min_commission: 最低手续费，默认 5.0
    """

    def __init__(
        self,
        session: PaperSession,
        commission_rate: float = 0.001,
        slippage_pct: float = 0.0005,
        min_commission: float = 5.0,
    ) -> None:
        self._session = session
        self._commission_rate = commission_rate
        self._slippage_pct = slippage_pct
        self._min_commission = min_commission

        # 构建共享 StrategyContext
        self._context = StrategyContext(
            symbol=session.symbol,
            timeframe=session.timeframe,
            initial_cash=session.initial_cash,
            cash=session.cash,
            positions=session.positions,
        )

    def process_bar(self, strategy: BaseStrategy, bar: OHLCVBar) -> None:
        """处理单根 K 线：同步上下文 → 调用策略 → 撮合订单 → 更新会话.

        Args:
            strategy: 策略实例
            bar: 当前 K 线数据
        """
        sess = self._session
        ctx = self._context

        # 同步会话状态到上下文
        ctx.cash = sess.cash
        ctx.positions = sess.positions
        ctx.orders.clear()

        # 调用策略
        strategy.on_bar(bar, ctx)

        # 撮合待执行订单
        for order in ctx.orders:
            self._execute_order(order, bar)

        # 更新会话元信息
        sess.bars_processed += 1
        sess.last_bar_at = bar.timestamp
        sess.portfolio_history.append(
            sess.portfolio_value({bar.symbol: bar.close})
        )

    def _execute_order(self, order: Order, bar: OHLCVBar) -> None:
        """撮合单笔订单（市价单，以收盘价加滑点成交）.

        Args:
            order: 待执行订单
            bar: 当前 K 线（用于定价）
        """
        sess = self._session

        if order.side == OrderSide.BUY:
            fill_price = bar.close * (1.0 + self._slippage_pct)
            trade_value = fill_price * order.quantity
            commission = max(self._commission_rate * trade_value, self._min_commission)
            total_cost = trade_value + commission

            # 资金不足则跳过
            if total_cost > sess.cash:
                return

            sess.cash -= total_cost

            # 更新持仓（加权平均成本）
            existing = sess.positions.get(order.symbol)
            if existing is None:
                sess.positions[order.symbol] = Position(
                    symbol=order.symbol,
                    quantity=order.quantity,
                    avg_price=fill_price,
                )
            else:
                total_qty = existing.quantity + order.quantity
                existing.avg_price = (
                    existing.avg_price * existing.quantity + fill_price * order.quantity
                ) / total_qty
                existing.quantity = total_qty

        elif order.side == OrderSide.SELL:
            fill_price = bar.close * (1.0 - self._slippage_pct)
            existing = sess.positions.get(order.symbol)
            if existing is None or existing.quantity < order.quantity:
                return

            trade_value = fill_price * order.quantity
            commission = max(self._commission_rate * trade_value, self._min_commission)
            proceeds = trade_value - commission

            entry_price = existing.avg_price
            existing.quantity -= order.quantity
            if existing.quantity == 0:
                del sess.positions[order.symbol]

            sess.cash += proceeds

            # 记录交易
            sess.trades.append(
                TradeRecord(
                    symbol=order.symbol,
                    side="sell",
                    entry_time=sess.started_at,
                    exit_time=bar.timestamp,
                    entry_price=entry_price,
                    exit_price=fill_price,
                    quantity=order.quantity,
                    commission=commission,
                )
            )
