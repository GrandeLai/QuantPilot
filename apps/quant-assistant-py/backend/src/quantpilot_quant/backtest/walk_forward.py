"""Walk-Forward 滚动步进回测引擎.

执行逻辑（每个窗口）：

  全量 bars（时间升序）
  │
  ├─ [train_start : train_end]   训练窗口
  │      ↓ Step 1：OptimizationEngine.grid_search → 最优参数
  │      ↓ Step 2：与测试集一起传入 BacktestEngine（无 gap），
  │                作为指标热身期（EMA/ATR 等滚动指标在此积累状态）
  │
  ├─ (gap_size 根 K 线)          物理隔离带 ← 强制剔除，绝不传入引擎
  │      防止因子计算窗口（如 EMA-20）跨边界污染测试期信号
  │
  └─ [test_start : test_end]    测试窗口（OOS 评估区间）
         ↓ Step 3：从 BacktestEngine 完整结果中截取该段净值 / 交易
         ↓ 重新调用 calculate_metrics → 本窗口 BacktestResult

  各窗口结束后，将所有测试期净值序列复利链式拼接 → 聚合 BacktestMetrics。

接口兼容性：
  - 内部调用 BacktestEngine.run()，不改动现有引擎任何代码；
  - BacktestResult / BacktestMetrics / TradeRecord 格式完全不变；
  - 复用 research/validation.py 的 build_walk_forward_windows()。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from loguru import logger

from quantpilot_quant.backtest.engine import BacktestConfig, BacktestEngine, BacktestResult
from quantpilot_quant.backtest.metrics import BacktestMetrics, TradeRecord, calculate_metrics
from quantpilot_common.data.models import OHLCVBar
from quantpilot_quant.research.validation import TimeSeriesValidationConfig, build_walk_forward_windows

# OptimizationEngine + ParamGrid imports are lazy (inside _search_best_params)
# to avoid circular import with optimize.engine which imports backtest.engine.

if TYPE_CHECKING:
    from quantpilot_quant.strategy.base import BaseStrategy


# ── 数据结构 ──────────────────────────────────────────────────────────────────


@dataclass
class WalkForwardConfig:
    """Walk-Forward 滚动步进参数.

    Attributes
    ----------
    train_size:
        训练窗口大小（根 K 线数）。用于两个目的：
        ① 在此窗口内做参数网格搜索；② 作为测试期的指标热身数据。
    test_size:
        测试窗口大小（根 K 线数）。这是实际 OOS 评估区间，
        回测指标仅基于此段计算。
    step_size:
        每次向前滚动的步进根数。step_size < test_size 时窗口重叠，
        step_size == test_size 时窗口紧密相邻（标准非重叠 WF）。
    gap_size:
        物理隔离带根数（train_end 与 test_start 之间强制丢弃）。
        设置原则：≥ 策略使用的最长指标窗口（如 EMA-20 → gap_size=20），
        确保因子计算完全无法"看到"测试期数据。默认 5。
    """

    train_size: int = 252
    test_size: int = 63
    step_size: int = 21
    gap_size: int = 5


@dataclass
class WalkForwardWindowResult:
    """单个 Walk-Forward 窗口的回测结果.

    Attributes
    ----------
    window_idx:
        窗口序号（从 0 开始）。
    train_range:
        训练区间 ``(start, end)`` 闭区间行索引（相对全量 bars）。
    gap_range:
        隔离带 ``(start, end)`` 闭区间行索引，仅记录位置，
        这段数据从不传入任何引擎。
    test_range:
        测试区间 ``(start, end)`` 闭区间行索引。
    best_params:
        本窗口训练集上网格搜索得到的最优参数（按 Sharpe 排序）。
        若未提供 param_grid 则等于策略的 default_params。
    result:
        测试期回测结果，格式与 ``BacktestResult`` 完全一致，
        metrics.initial_cash 为训练结束时的实际组合价值。
    """

    window_idx: int
    train_range: tuple[int, int]
    gap_range: tuple[int, int]
    test_range: tuple[int, int]
    best_params: dict[str, Any]
    result: BacktestResult


@dataclass
class WalkForwardResult:
    """Walk-Forward 完整回测结果.

    Attributes
    ----------
    config:
        沿用的基础回测配置（initial_cash / commission_rate 等）。
    wf_config:
        Walk-Forward 专属配置（窗口大小、步进、隔离带）。
    windows:
        各窗口的详细回测结果列表，按时间顺序排列。
    aggregated_metrics:
        跨所有测试窗口的聚合指标。净值序列采用复利链式拼接（见 _aggregate），
        与现有 BacktestMetrics 格式完全一致，可直接复用下游展示逻辑。
    all_trades:
        所有测试窗口的交易记录（按出场时间升序），去除训练期交易。
    n_windows:
        成功执行的窗口数量。
    strategy_cls_name:
        策略类名（用于日志和报告）。
    start_time / end_time:
        整个 Walk-Forward 回测的墙钟开始/结束时间。
    """

    config: BacktestConfig
    wf_config: WalkForwardConfig
    windows: list[WalkForwardWindowResult]
    aggregated_metrics: BacktestMetrics
    all_trades: list[TradeRecord]
    n_windows: int
    strategy_cls_name: str
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def duration_seconds(self) -> float:
        """整体运行耗时（秒）."""
        return (self.end_time - self.start_time).total_seconds()


# ── 引擎 ──────────────────────────────────────────────────────────────────────


class WalkForwardEngine:
    """Walk-Forward 滚动步进回测引擎.

    **设计原则**：
    - 完全复用 ``BacktestEngine``，不修改任何已有代码；
    - 每个窗口独立运行，策略实例隔离，initial_cash 各自归零；
    - gap 隔离带通过复用 ``build_walk_forward_windows(embargo_size=gap_size)``
      物理实现，gap 内的 K 线从不出现在任何引擎调用中。

    **性能提示**：
    每个窗口内部会先运行 ``len(param_grid_combinations)`` 次独立回测（参数搜索），
    再额外运行 1 次热身+测试回测。param_grid 组合数建议控制在 50 以内以保证响应速度；
    如需更大搜索空间，改用 ``OptimizationEngine.bayesian_search``（未来扩展点）。

    使用示例::

        engine = WalkForwardEngine(
            config=BacktestConfig(symbol="BTC-USDT", timeframe="1d", initial_cash=100_000),
            wf_config=WalkForwardConfig(train_size=200, test_size=50, step_size=25, gap_size=20),
        )
        result = engine.run(
            MACrossoverStrategy,
            bars,
            param_grid={"fast_period": [5, 10, 20], "slow_period": [20, 30, 60]},
        )
        print(result.aggregated_metrics.sharpe_ratio)
        for wr in result.windows:
            print(wr.window_idx, wr.best_params, wr.result.metrics.total_return)
    """

    def __init__(self, config: BacktestConfig, wf_config: WalkForwardConfig) -> None:
        self._config = config
        self._wf_config = wf_config

    def run(
        self,
        strategy_cls: type[BaseStrategy],
        bars: list[OHLCVBar],
        param_grid: dict[str, list[Any]] | None = None,
    ) -> WalkForwardResult:
        """执行 Walk-Forward 回测.

        Parameters
        ----------
        strategy_cls:
            策略**类**（不是实例）。引擎在每个窗口内独立实例化，
            确保不同窗口之间的策略内部状态（deque、指标缓冲等）完全隔离。
        bars:
            全量 K 线数据，乱序亦可（引擎内部排序）。
        param_grid:
            参数搜索空间，格式 ``{"param_name": [val1, val2, ...]}``。
            为 ``None`` 或空字典时跳过网格搜索，直接使用策略的 ``default_params``。

        Returns
        -------
        WalkForwardResult
            含各窗口详细结果和跨窗口聚合指标。

        Raises
        ------
        ValueError
            全量 K 线数量不足以构建哪怕一个窗口。
        """
        start_time = datetime.now(UTC)
        bars_sorted = sorted(bars, key=lambda b: b.timestamp)
        n = len(bars_sorted)
        wf = self._wf_config

        # 复用 research/validation.py 的窗口切割（gap_size → embargo_size）
        validation_cfg = TimeSeriesValidationConfig(
            train_size=wf.train_size,
            test_size=wf.test_size,
            step_size=wf.step_size,
            embargo_size=wf.gap_size,
        )
        windows = build_walk_forward_windows(total_rows=n, config=validation_cfg)

        min_bars = wf.train_size + wf.gap_size + wf.test_size
        if not windows:
            raise ValueError(
                f"K 线数量不足（{n} 根），无法构建 Walk-Forward 窗口。"
                f"至少需要 {min_bars} 根 K 线。"
            )

        window_results: list[WalkForwardWindowResult] = []

        for i, win in enumerate(windows):
            train_bars = bars_sorted[win.train_start : win.train_end + 1]
            test_bars  = bars_sorted[win.test_start  : win.test_end  + 1]
            gap_start  = win.train_end + 1
            gap_end    = win.test_start - 1

            logger.info(
                "[WalkForward] 窗口 {}/{}: train=[{},{}]({}) gap=[{},{}]({}) test=[{},{}]({})",
                i + 1, len(windows),
                win.train_start, win.train_end, len(train_bars),
                gap_start, gap_end, wf.gap_size,
                win.test_start, win.test_end, len(test_bars),
            )

            if not test_bars:
                logger.warning(f"[WalkForward] 窗口 {i} 测试集为空，跳过")
                continue

            # ── Step 1：训练集参数搜索 ────────────────────────────────────
            best_params = self._search_best_params(
                strategy_cls=strategy_cls,
                train_bars=train_bars,
                param_grid=param_grid or {},
            )

            # ── Step 2：热身 + 测试（gap 被自然剔除，不含任何 gap 根 K 线）
            strategy = self._make_strategy(strategy_cls, best_params)
            warmup_and_test = train_bars + test_bars   # gap 已物理丢弃
            full_result = BacktestEngine(self._config).run(strategy, warmup_and_test)

            # ── Step 3：截取测试期指标，重新计算 BacktestResult ──────────
            test_result = self._slice_to_test(
                full_result=full_result,
                n_train=len(train_bars),
                test_start_ts=test_bars[0].timestamp,
            )

            window_results.append(WalkForwardWindowResult(
                window_idx=i,
                train_range=(win.train_start, win.train_end),
                gap_range=(gap_start, gap_end),
                test_range=(win.test_start, win.test_end),
                best_params=best_params,
                result=test_result,
            ))

        # ── Step 4：聚合 ───────────────────────────────────────────────────
        aggregated_metrics, all_trades = self._aggregate(window_results)
        end_time = datetime.now(UTC)

        logger.info(
            "[WalkForward] 完成 {} 个窗口 | 聚合 Sharpe={:.3f} | "
            "聚合总收益={:.2%} | 总交易数={}",
            len(window_results),
            aggregated_metrics.sharpe_ratio,
            aggregated_metrics.total_return,
            len(all_trades),
        )

        return WalkForwardResult(
            config=self._config,
            wf_config=wf,
            windows=window_results,
            aggregated_metrics=aggregated_metrics,
            all_trades=all_trades,
            n_windows=len(window_results),
            strategy_cls_name=strategy_cls.__name__,
            start_time=start_time,
            end_time=end_time,
        )

    # ── 私有方法 ──────────────────────────────────────────────────────────────

    def _search_best_params(
        self,
        strategy_cls: type[BaseStrategy],
        train_bars: list[OHLCVBar],
        param_grid: dict[str, list[Any]],
    ) -> dict[str, Any]:
        """在训练集上执行网格搜索，返回 Sharpe 最优参数.

        若 param_grid 为空或训练数据不足，则直接返回策略的 default_params。
        搜索失败（所有组合 Sharpe=-999）时同样回退到 default_params。
        """
        defaults: dict[str, Any] = dict(getattr(strategy_cls, "default_params", {}))

        if not param_grid or len(train_bars) < 2:
            return defaults

        # Lazy import to break circular dependency: optimize.engine imports
        # backtest.engine which imports backtest.__init__ which imports this module.
        from quantpilot_quant.optimize.engine import OptimizationEngine, ParamGrid

        opt = OptimizationEngine(self._config, train_bars)
        results = opt.grid_search(strategy_cls, ParamGrid(param_grid))

        # Sharpe > -900 才算有效结果（-999 是 OptimizationEngine 的失败标记）
        valid = [r for r in results if r.sharpe_ratio > -900]
        if valid:
            logger.debug(
                "[WalkForward] 参数搜索: {} 组合，最优 Sharpe={:.3f} params={}",
                len(results), valid[0].sharpe_ratio, valid[0].params,
            )
            return valid[0].params

        logger.warning("[WalkForward] 参数搜索无有效结果，回退到 default_params")
        return defaults

    @staticmethod
    def _make_strategy(
        strategy_cls: type[BaseStrategy],
        params: dict[str, Any],
    ) -> BaseStrategy:
        """实例化策略，优先关键字参数传入，失败时退化为 default_params 注入."""
        try:
            return strategy_cls(**params)
        except TypeError:
            strategy = strategy_cls()
            strategy.default_params = {
                **dict(getattr(strategy_cls, "default_params", {})),
                **params,
            }
            return strategy

    def _slice_to_test(
        self,
        full_result: BacktestResult,
        n_train: int,
        test_start_ts: object,
    ) -> BacktestResult:
        """从「热身+测试」完整结果中截取测试期净值和交易，重新计算指标.

        净值基准：取训练结束时刻的实际组合价值（即 portfolio_values[n_train-1]），
        而非 initial_cash。这样测试期收益率反映的是从训练结束状态出发的真实 OOS 表现。

        trades 过滤规则：出场时间 >= test_start_ts 的交易才算测试期交易，
        跨越 train/test 边界开仓、测试期平仓的交易亦纳入统计。
        """
        all_pv = full_result.metrics.portfolio_values

        # 截取测试期净值序列（不含训练期）
        test_pv = all_pv[n_train:] if n_train < len(all_pv) else list(all_pv)

        # 测试期初始资金 = 训练结束时组合净值（各窗口独立，不跨窗口传递资金）
        base_value = (
            all_pv[n_train - 1]
            if (n_train > 0 and all_pv)
            else self._config.initial_cash
        )

        # 筛选测试期交易（按出场时间判断）
        test_trades: list[TradeRecord] = [
            t for t in full_result.trades
            if t.exit_time >= test_start_ts  # type: ignore[operator]
        ]

        # 重新计算测试期绩效指标
        new_metrics = calculate_metrics(
            portfolio_values=test_pv,
            trades=test_trades,
            initial_cash=base_value,
            risk_free_rate=self._config.risk_free_rate,
        )

        # 补充日期区间（从交易记录推断）
        if test_trades:
            new_metrics.start_date = test_trades[0].entry_time.isoformat()
            new_metrics.end_date   = test_trades[-1].exit_time.isoformat()

        return BacktestResult(
            config=full_result.config,
            metrics=new_metrics,
            trades=test_trades,
            bars_processed=len(test_pv),
            start_time=full_result.start_time,
            end_time=full_result.end_time,
        )

    def _aggregate(
        self,
        window_results: list[WalkForwardWindowResult],
    ) -> tuple[BacktestMetrics, list[TradeRecord]]:
        """将所有测试窗口的净值序列复利链式拼接，计算跨窗口聚合指标.

        **链式拼接规则**：
        每个窗口的净值序列先归一化为相对倍数（v / window_start），
        再乘以当前链末尾的绝对净值值，使各窗口在量纲上连续接续。

        示例（initial_cash=10000）：
          窗口 1 测试期净值: [10200, 10400, 10100]  → 末值 10100
          窗口 2 测试期净值: [9800, 10300, 10500]   → 相对倍数 [1.0, 1.051, 1.071]
          链式结果:          10100 × [1.0, 1.051, 1.071] = [10100, 10615, 10818]

        这等价于：每个窗口末尾将资金全部取出，下个窗口开始时按相同策略重新投入。
        """
        chained_pv: list[float] = []
        current_base = self._config.initial_cash
        all_trades: list[TradeRecord] = []

        for wr in window_results:
            pv = wr.result.metrics.portfolio_values
            if not pv:
                continue

            window_start = pv[0] if pv[0] != 0.0 else self._config.initial_cash
            chained_pv.extend(current_base * v / window_start for v in pv)
            current_base = chained_pv[-1]
            all_trades.extend(wr.result.trades)

        all_trades.sort(key=lambda t: t.exit_time)

        aggregated = calculate_metrics(
            portfolio_values=chained_pv,
            trades=all_trades,
            initial_cash=self._config.initial_cash,
            risk_free_rate=self._config.risk_free_rate,
        )

        # 补充聚合日期区间
        if window_results:
            aggregated.start_date = window_results[0].result.metrics.start_date
            aggregated.end_date   = window_results[-1].result.metrics.end_date

        return aggregated, all_trades
