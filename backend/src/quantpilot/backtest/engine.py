"""事件驱动回测引擎.

架构：DataHandler → Strategy → Portfolio → ExecutionHandler
支持：日线级、分钟级回测，滑点模型，手续费，止损/止盈。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from loguru import logger

from quantpilot.backtest.metrics import BacktestMetrics, TradeRecord, calculate_metrics
from quantpilot_common.data.models import OHLCVBar
from quantpilot.strategy.base import (
    Order,
    OrderSide,
    OrderType,
    Position,
    StrategyContext,
)

if TYPE_CHECKING:
    from quantpilot.strategy.base import BaseStrategy


@dataclass
class BacktestConfig:
    """回测配置参数."""

    symbol: str
    timeframe: str
    initial_cash: float = 1_000_000.0
    commission_rate: float = 0.001    # 手续费率（双边）
    slippage_pct: float = 0.0005     # 滑点比例
    min_commission: float = 5.0      # 最低手续费（元/次）
    risk_free_rate: float = 0.02     # 年化无风险利率
    # 基础风控
    stop_loss_pct: float | None = None    # 止损百分比（如 0.05 表示 5%）
    take_profit_pct: float | None = None  # 止盈百分比
    max_position_pct: float = 1.0         # 最大单标的持仓占比


@dataclass
class BacktestResult:
    """回测结果."""

    config: BacktestConfig
    metrics: BacktestMetrics
    trades: list[TradeRecord]
    bars_processed: int
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def duration_seconds(self) -> float:
        return (self.end_time - self.start_time).total_seconds()


class BacktestEngine:
    """事件驱动回测引擎.

    使用方式：
        engine = BacktestEngine(config)
        result = engine.run(strategy, bars)
    """

    def __init__(self, config: BacktestConfig) -> None:
        self._config = config

    def run(
        self,
        strategy: BaseStrategy,
        bars: list[OHLCVBar],
    ) -> BacktestResult:
        """执行回测.

        Args:
            strategy: 策略实例
            bars: K 线数据（升序排列）

        Returns:
            BacktestResult 包含绩效指标和交易记录
        """
        start_time = datetime.now(UTC)
        cfg = self._config

        # 初始化上下文
        ctx = StrategyContext(
            symbol=cfg.symbol,
            timeframe=cfg.timeframe,
            initial_cash=cfg.initial_cash,
        )

        # 初始化策略
        strategy.on_init(ctx)

        portfolio_values: list[float] = []
        completed_trades: list[TradeRecord] = []
        # 记录开仓信息用于计算平仓 PnL
        open_positions: dict[str, dict[str, object]] = {}  # symbol -> {entry_price, entry_time, qty}

        bars_sorted = sorted(bars, key=lambda b: b.timestamp)

        for bar in bars_sorted:
            # 清空本轮订单
            ctx.orders.clear()

            # 调用策略
            strategy.on_bar(bar, ctx)

            # 执行订单（市价单立即以当前收盘价成交）
            for order in ctx.orders:
                self._execute_order(order, bar, ctx, completed_trades, open_positions, cfg)

            # 检查止损/止盈
            if cfg.stop_loss_pct or cfg.take_profit_pct:
                self._check_stop_take(bar, ctx, completed_trades, open_positions, cfg)

            # 计算当日组合净值
            pv = ctx.cash + sum(
                pos.quantity * bar.close
                for pos in ctx.positions.values()
                if pos.symbol == bar.symbol
            )
            portfolio_values.append(pv)

        # 策略停止
        strategy.on_stop(ctx)

        # 强制平仓（回测结束时平掉所有持仓）
        if bars_sorted and ctx.positions:
            last_bar = bars_sorted[-1]
            for sym, pos in list(ctx.positions.items()):
                if pos.quantity > 0:
                    pnl, commission, slippage = self._calc_pnl(
                        entry_price=pos.avg_price,
                        exit_price=last_bar.close,
                        quantity=pos.quantity,
                        cfg=cfg,
                    )
                    entry_info = open_positions.get(sym, {})
                    completed_trades.append(TradeRecord(
                        symbol=sym,
                        side="buy",
                        entry_time=entry_info.get("entry_time", last_bar.timestamp),  # type: ignore[arg-type]
                        exit_time=last_bar.timestamp,
                        entry_price=pos.avg_price,
                        exit_price=last_bar.close,
                        quantity=pos.quantity,
                        commission=commission,
                        slippage=slippage,
                    ))

        # 计算绩效
        metrics = calculate_metrics(
            portfolio_values=portfolio_values,
            trades=completed_trades,
            initial_cash=cfg.initial_cash,
            risk_free_rate=cfg.risk_free_rate,
        )

        if bars_sorted:
            metrics.start_date = bars_sorted[0].timestamp.isoformat()
            metrics.end_date = bars_sorted[-1].timestamp.isoformat()

        end_time = datetime.now(UTC)
        logger.info(
            f"[Backtest] {cfg.symbol} {cfg.timeframe} 完成，"
            f"{len(bars_sorted)} 根 K 线，{len(completed_trades)} 笔交易，"
            f"收益率 {metrics.total_return:.2%}，Sharpe {metrics.sharpe_ratio:.2f}"
        )

        return BacktestResult(
            config=cfg,
            metrics=metrics,
            trades=completed_trades,
            bars_processed=len(bars_sorted),
            start_time=start_time,
            end_time=end_time,
        )

    def _execute_order(
        self,
        order: Order,
        bar: OHLCVBar,
        ctx: StrategyContext,
        trades: list[TradeRecord],
        open_positions: dict[str, dict[str, object]],
        cfg: BacktestConfig,
    ) -> None:
        """执行单笔订单（市价单以收盘价成交）."""
        exec_price = bar.close

        # 滑点：买入加价，卖出减价
        if order.side == OrderSide.BUY:
            exec_price *= 1 + cfg.slippage_pct
        else:
            exec_price *= 1 - cfg.slippage_pct

        commission = max(exec_price * order.quantity * cfg.commission_rate, cfg.min_commission)

        if order.side == OrderSide.BUY:
            cost = exec_price * order.quantity + commission
            if cost > ctx.cash:
                logger.debug(f"[Backtest] 资金不足，跳过买入 {order.symbol}")
                return

            ctx.cash -= cost
            pos = ctx.positions.get(order.symbol)
            if pos is None:
                ctx.positions[order.symbol] = Position(
                    symbol=order.symbol,
                    quantity=order.quantity,
                    avg_price=exec_price,
                )
                open_positions[order.symbol] = {
                    "entry_price": exec_price,
                    "entry_time": bar.timestamp,
                    "qty": order.quantity,
                }
            else:
                # 加仓：计算加权平均价格
                total_qty = pos.quantity + order.quantity
                pos.avg_price = (pos.quantity * pos.avg_price + order.quantity * exec_price) / total_qty
                pos.quantity = total_qty

        elif order.side == OrderSide.SELL:
            pos = ctx.positions.get(order.symbol)
            if pos is None or pos.quantity <= 0:
                logger.debug(f"[Backtest] 无持仓，跳过卖出 {order.symbol}")
                return

            sell_qty = min(order.quantity, pos.quantity)
            pnl, commission, slippage = self._calc_pnl(
                entry_price=pos.avg_price,
                exit_price=exec_price,
                quantity=sell_qty,
                cfg=cfg,
            )

            entry_info = open_positions.get(order.symbol, {})
            trades.append(TradeRecord(
                symbol=order.symbol,
                side="buy",
                entry_time=entry_info.get("entry_time", bar.timestamp),  # type: ignore[arg-type]
                exit_time=bar.timestamp,
                entry_price=pos.avg_price,
                exit_price=exec_price,
                quantity=sell_qty,
                commission=commission,
                slippage=slippage,
            ))

            ctx.cash += exec_price * sell_qty - commission
            pos.quantity -= sell_qty
            if pos.quantity <= 0:
                del ctx.positions[order.symbol]
                open_positions.pop(order.symbol, None)

    def _check_stop_take(
        self,
        bar: OHLCVBar,
        ctx: StrategyContext,
        trades: list[TradeRecord],
        open_positions: dict[str, dict[str, object]],
        cfg: BacktestConfig,
    ) -> None:
        """检查并执行止损/止盈."""
        for sym, pos in list(ctx.positions.items()):
            if pos.quantity <= 0:
                continue
            ret = (bar.close - pos.avg_price) / pos.avg_price
            triggered = False

            if cfg.stop_loss_pct and ret <= -cfg.stop_loss_pct:
                logger.debug(f"[Backtest] 止损触发 {sym} ret={ret:.2%}")
                triggered = True
            elif cfg.take_profit_pct and ret >= cfg.take_profit_pct:
                logger.debug(f"[Backtest] 止盈触发 {sym} ret={ret:.2%}")
                triggered = True

            if triggered:
                fake_order = Order(
                    symbol=sym,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=pos.quantity,
                    comment="止损/止盈",
                )
                self._execute_order(fake_order, bar, ctx, trades, open_positions, cfg)

    @staticmethod
    def _calc_pnl(
        entry_price: float, exit_price: float, quantity: float, cfg: BacktestConfig
    ) -> tuple[float, float, float]:
        """计算单笔 PnL（净）.

        Returns: (net_pnl, commission, slippage)
        """
        slippage_cost = exit_price * quantity * cfg.slippage_pct
        commission = max(exit_price * quantity * cfg.commission_rate, cfg.min_commission)
        gross_pnl = (exit_price - entry_price) * quantity
        net_pnl = gross_pnl - commission - slippage_cost
        return net_pnl, commission, slippage_cost
