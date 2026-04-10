"""多策略组合管理器."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
from loguru import logger

from quantpilot.data.models import OHLCVBar
from quantpilot.paper.engine import PaperSession, PaperTradingEngine

if TYPE_CHECKING:
    from quantpilot.strategy.base import BaseStrategy


def _max_drawdown(values: list[float]) -> float:
    """计算最大回撤百分比（返回负数，如 -12.5 表示 12.5% 回撤）."""
    if len(values) < 2:
        return 0.0
    arr = np.array(values, dtype=float)
    peak = np.maximum.accumulate(arr)
    safe_peak = np.where(peak > 0, peak, 1.0)
    drawdowns = (arr - peak) / safe_peak
    return float(drawdowns.min()) * 100


def _sharpe_ratio(values: list[float], periods_per_year: int = 252) -> float:
    """计算年化夏普比率（无风险利率 = 0）."""
    if len(values) < 3:
        return 0.0
    arr = np.array(values, dtype=float)
    prev = arr[:-1]
    safe_prev = np.where(prev > 0, prev, 1.0)
    returns = (arr[1:] - prev) / safe_prev
    std = float(np.std(returns))
    if std == 0.0:
        return 0.0
    return float(np.mean(returns)) / std * np.sqrt(periods_per_year)


@dataclass
class StrategySlot:
    """单个策略槽位."""

    name: str
    session: PaperSession
    allocation: float
    engine: PaperTradingEngine = field(init=False)
    strategy: Any = field(init=False, default=None)
    pnl_history: list[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.engine = PaperTradingEngine(self.session)


class PortfolioManager:
    """管理 N 个并发运行的模拟盘策略."""

    def __init__(self, total_cash: float = 1_000_000.0) -> None:
        self._total_cash = total_cash
        self._allocated = 0.0
        self.strategies: dict[str, StrategySlot] = {}
        self._lock = threading.Lock()

    def add_strategy(
        self,
        name: str,
        strategy: BaseStrategy,
        symbol: str,
        timeframe: str,
        allocation: float,
    ) -> None:
        """添加策略到组合."""
        with self._lock:
            if self._allocated + allocation > self._total_cash:
                raise ValueError(
                    f"资金不足: 已分配 {self._allocated:.0f}, 新增 {allocation:.0f}, "
                    f"总额 {self._total_cash:.0f}"
                )
            sess = PaperSession(symbol=symbol, timeframe=timeframe, initial_cash=allocation)
            slot = StrategySlot(name=name, session=sess, allocation=allocation)
            slot.strategy = strategy
            slot.engine = PaperTradingEngine(sess)
            slot.strategy.on_init(slot.engine._context)
            self.strategies[name] = slot
            self._allocated += allocation
            logger.info(f"[Portfolio] 策略 '{name}' 已加入组合, 分配资金={allocation:.0f}")

    def remove_strategy(self, name: str) -> None:
        """从组合中移除策略并回收资金."""
        with self._lock:
            if name not in self.strategies:
                return
            slot = self.strategies.pop(name)
            self._allocated -= slot.allocation
            logger.info(f"[Portfolio] 策略 '{name}' 已移除")

    def process_bar(self, strategy_name: str, bar: OHLCVBar) -> None:
        """向指定策略推送一根新K线."""
        slot = self.strategies.get(strategy_name)
        if slot is None:
            return
        slot.engine.process_bar(slot.strategy, bar)
        pv = slot.session.portfolio_value({bar.symbol: bar.close})
        slot.pnl_history.append(pv)

    def summary(self, current_prices: dict[str, float]) -> dict[str, Any]:
        """返回组合总览：各策略状态 + 合并持仓价值."""
        total_value = 0.0
        strategies_info = []
        for name, slot in self.strategies.items():
            sess = slot.session
            pv = sess.portfolio_value(current_prices)
            total_value += pv
            pnl = pv - slot.allocation
            pnl_pct = pnl / slot.allocation * 100 if slot.allocation > 0 else 0.0
            strategies_info.append({
                "name": name,
                "symbol": sess.symbol,
                "allocation": slot.allocation,
                "portfolio_value": round(pv, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2),
                "bars_processed": sess.bars_processed,
                "trades_count": len(sess.trades),
                "max_drawdown": round(_max_drawdown(slot.pnl_history), 2),
                "sharpe_ratio": round(_sharpe_ratio(slot.pnl_history), 3),
            })
        return {
            "total_cash": self._total_cash,
            "total_allocated": self._allocated,
            "total_portfolio_value": round(total_value, 2),
            "strategies": strategies_info,
        }

    def correlation_matrix(self) -> dict[str, dict[str, float]]:
        """计算各策略净值序列之间的相关性矩阵."""
        names = list(self.strategies.keys())
        histories = {name: self.strategies[name].pnl_history for name in names}
        min_len = min((len(h) for h in histories.values()), default=0)
        if min_len < 2:
            return {n: {m: 1.0 if n == m else 0.0 for m in names} for n in names}

        matrix: dict[str, dict[str, float]] = {}
        for n1 in names:
            matrix[n1] = {}
            h1 = np.array(histories[n1][:min_len])
            for n2 in names:
                h2 = np.array(histories[n2][:min_len])
                if np.std(h1) == 0 or np.std(h2) == 0:
                    corr = 1.0 if n1 == n2 else 0.0
                else:
                    corr = float(np.corrcoef(h1, h2)[0, 1])
                matrix[n1][n2] = round(corr, 4)
        return matrix
