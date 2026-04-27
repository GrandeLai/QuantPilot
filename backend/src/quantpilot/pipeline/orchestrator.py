"""全自动化量化策略 Pipeline 编排器."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from loguru import logger


class PipelineStatus(str, Enum):
    """Pipeline 整体状态."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


STEP_LABELS: dict[str, str] = {
    "data_check": "数据检查",
    "data_fetch": "数据拉取",
    "ml_train": "因子计算 & ML 训练",
    "signal_gen": "信号生成",
}


@dataclass
class StepResult:
    """单个 Pipeline 步骤的执行结果."""

    name: str
    label: str
    status: str = "pending"   # pending | running | done | error | skipped
    message: str = ""
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineJobState:
    """Pipeline 任务完整状态，包含所有步骤和最终结果."""

    job_id: str
    config: dict[str, Any]
    status: PipelineStatus = PipelineStatus.PENDING
    current_step: str = ""
    steps: list[StepResult] = field(default_factory=list)
    error: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    finished_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        """序列化为 JSON 兼容的字典，供 API 响应使用."""
        return {
            "job_id": self.job_id,
            "config": self.config,
            "status": self.status.value,
            "current_step": self.current_step,
            "steps": [
                {
                    "name": s.name,
                    "label": s.label,
                    "status": s.status,
                    "message": s.message,
                    "detail": s.detail,
                }
                for s in self.steps
            ],
            "error": self.error,
            "result": self.result,
            "created_at": self.created_at,
            "finished_at": self.finished_at,
        }


def make_job(config: dict[str, Any]) -> PipelineJobState:
    """Create initialized PipelineJobState with pending steps.

    Args:
        config: Pipeline 运行参数字典，需包含 symbol 等字段。

    Returns:
        已初始化的 PipelineJobState，包含全部 pending 步骤。
    """
    steps = [StepResult(name=k, label=v) for k, v in STEP_LABELS.items()]
    return PipelineJobState(
        job_id=str(uuid.uuid4())[:8],
        config=config,
        steps=steps,
    )


# 各基础时间框架对应的更高时间框架列表
_HIGHER_TF: dict[str, list[str]] = {
    "5m":  ["15m", "1h", "4h"],
    "15m": ["1h", "4h", "1d"],
    "1h":  ["4h", "1d"],
    "4h":  ["1d", "1w"],
    "1d":  ["1w"],
    "1w":  [],
}


class PipelineOrchestrator:
    """全自动化量化策略 Pipeline：数据检查 → 数据拉取 → ML 训练 → 信号生成."""

    def __init__(self, storage: Any) -> None:
        """初始化编排器.

        Args:
            storage: MarketDataStorage 实例。
        """
        self._storage = storage

    async def run(self, state: PipelineJobState) -> None:
        """异步运行 Pipeline：data_check → data_fetch（如需）→ ml_train → signal_gen.

        Args:
            state: 任务状态对象，原地修改并反映各步骤进展。
        """
        state.status = PipelineStatus.RUNNING
        try:
            cfg = state.config
            symbol: str = cfg["symbol"]
            timeframe: str = cfg.get("timeframe", "1d")
            start_date: str = cfg.get("start_date", "2022-01-01")
            end_date: str = cfg.get("end_date", datetime.now().strftime("%Y-%m-%d"))

            loop = asyncio.get_running_loop()

            # Step 1: data_check（同步 → executor）
            bar_count: int = await loop.run_in_executor(
                None,
                self._step_data_check,
                state, symbol, timeframe, start_date, end_date,
            )

            # Step 2: data_fetch — 仅在本地 K 线不足 50 根时才拉取
            if bar_count < 50:
                await loop.run_in_executor(
                    None,
                    self._step_data_fetch,
                    state, symbol, timeframe, start_date, end_date,
                )
            else:
                s = self._get_step(state, "data_fetch")
                s.status = "skipped"
                s.message = f"本地已有 {bar_count} 根 K 线，跳过拉取"

            # Step 3: ml_train（同步 → executor）
            train_result: dict[str, Any] = await loop.run_in_executor(
                None,
                self._step_ml_train,
                state, symbol, timeframe,
            )

            # Step 4: signal_gen（异步 — SignalBroadcaster.publish 为 async）
            await self._step_signal_gen(state, symbol, train_result)

            state.status = PipelineStatus.DONE

        except Exception as exc:
            logger.exception("Pipeline error: job={}", state.job_id)
            state.status = PipelineStatus.ERROR
            state.error = str(exc)
            for s in state.steps:
                if s.status == "pending":
                    s.status = "error"
        finally:
            state.finished_at = datetime.now().isoformat()

    # ── 内部工具 ────────────────────────────────────────────────────────────

    def _get_step(self, state: PipelineJobState, name: str) -> StepResult:
        """按名称取步骤对象（找不到则报错）."""
        for s in state.steps:
            if s.name == name:
                return s
        raise KeyError(f"Step '{name}' not found in job {state.job_id}")

    # ── 各步骤实现 ──────────────────────────────────────────────────────────

    def _step_data_check(
        self,
        state: PipelineJobState,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
    ) -> int:
        """检查本地 K 线数量，返回 bar 数量.

        Args:
            state: 当前任务状态（原地更新步骤状态）。
            symbol: 交易标的，如 "BTC-USDT"。
            timeframe: K 线周期，如 "1d"。
            start_date: 起始日期字符串，格式 %Y-%m-%d。
            end_date: 结束日期字符串，格式 %Y-%m-%d。

        Returns:
            本地已有的 K 线条数。
        """
        step = self._get_step(state, "data_check")
        state.current_step = "data_check"
        step.status = "running"
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            df = self._storage.query_bars(
                symbol, timeframe, start=start_dt, end=end_dt
            )
            bar_count = len(df)
            step.status = "done"
            step.message = f"本地 K 线：{bar_count} 根"
            step.detail = {"bar_count": bar_count}
            logger.info("[Pipeline] data_check: {} {} → {} bars", symbol, timeframe, bar_count)
            return bar_count
        except Exception as exc:
            step.status = "error"
            step.message = str(exc)
            raise

    def _step_data_fetch(
        self,
        state: PipelineJobState,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
    ) -> None:
        """从 OKX 拉取历史 K 线并写入本地存储.

        Args:
            state: 当前任务状态（原地更新步骤状态）。
            symbol: 交易标的。
            timeframe: K 线周期。
            start_date: 起始日期字符串，格式 %Y-%m-%d。
            end_date: 结束日期字符串，格式 %Y-%m-%d。
        """
        from quantpilot.data.fetchers.okx_fetcher import OKXFetcher, normalize_symbol

        step = self._get_step(state, "data_fetch")
        state.current_step = "data_fetch"
        step.status = "running"
        try:
            start_d = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_d = datetime.strptime(end_date, "%Y-%m-%d").date()
            normalized = normalize_symbol(symbol)
            fetcher = OKXFetcher()
            bars = fetcher.fetch_ohlcv(normalized, timeframe, start_d, end_d)
            written = self._storage.upsert_bars(bars)
            step.status = "done"
            step.message = f"拉取并写入 {written} 根 K 线"
            step.detail = {"fetched": len(bars), "written": written}
            logger.info(
                "[Pipeline] data_fetch: {} {} → fetched={} written={}",
                symbol, timeframe, len(bars), written,
            )
        except Exception as exc:
            step.status = "error"
            step.message = str(exc)
            raise

    def _step_ml_train(
        self,
        state: PipelineJobState,
        symbol: str,
        timeframe: str,
    ) -> dict[str, Any]:
        """运行 CryptoResearchService.train_and_validate 并返回摘要字典.

        Args:
            state: 当前任务状态（原地更新步骤状态）。
            symbol: 交易标的。
            timeframe: K 线周期（作为 base_timeframe）。

        Returns:
            包含训练摘要所有字段的字典。
        """
        from quantpilot.research.service import CryptoResearchRequest, CryptoResearchService
        from quantpilot.research.validation import TimeSeriesValidationConfig

        step = self._get_step(state, "ml_train")
        state.current_step = "ml_train"
        step.status = "running"
        try:
            higher_tfs = _HIGHER_TF.get(timeframe, [])
            validation = TimeSeriesValidationConfig(
                train_size=200,
                test_size=50,
                step_size=50,
                embargo_size=5,
            )
            req = CryptoResearchRequest(
                symbol=symbol,
                base_timeframe=timeframe,
                higher_timeframes=higher_tfs,
                limit=500,
                validation=validation,
            )
            service = CryptoResearchService(self._storage)
            summary = service.train_and_validate(req)

            # feature_importance：按值降序取 top 15
            sorted_importance = dict(
                sorted(summary.feature_importance.items(), key=lambda x: x[1], reverse=True)[:15]
            )

            # window_metrics：转换为可序列化的字典列表
            window_metrics_list = [
                {
                    "window": idx,
                    "accuracy": wm.accuracy,
                    "strategy_return": wm.strategy_return,
                    "train_size": wm.train_end - wm.train_start + 1,
                    "test_size": wm.test_end - wm.test_start + 1,
                }
                for idx, wm in enumerate(summary.window_metrics)
            ]

            result: dict[str, Any] = {
                "feature_count": summary.feature_count,
                "validation_windows": summary.validation_windows,
                "mean_accuracy": summary.mean_accuracy,
                "mean_strategy_return": summary.mean_strategy_return,
                "latest_class_signal": summary.latest_class_signal,
                "latest_class_probabilities": summary.latest_class_probabilities,
                "feature_importance": sorted_importance,
                "window_metrics": window_metrics_list,
                "market_regime": summary.market_regime,
                "reversal_probability": summary.reversal_probability,
                "reversal_signal": summary.reversal_signal,
                "reversal_evidence": summary.reversal_evidence,
                "recommended_strategy_ids": summary.recommended_strategy_ids,
                "recommended_timeframes": summary.recommended_timeframes,
            }

            state.result.update(result)
            step.status = "done"
            step.message = (
                f"训练完成：{summary.validation_windows} 窗口，"
                f"均准确率 {summary.mean_accuracy:.2%}"
            )
            step.detail = {
                "feature_count": summary.feature_count,
                "validation_windows": summary.validation_windows,
                "mean_accuracy": summary.mean_accuracy,
            }
            logger.info(
                "[Pipeline] ml_train: {} {} → windows={} acc={:.2%}",
                symbol, timeframe, summary.validation_windows, summary.mean_accuracy,
            )
            return result
        except Exception as exc:
            step.status = "error"
            step.message = str(exc)
            raise

    async def _step_signal_gen(
        self,
        state: PipelineJobState,
        symbol: str,
        train_result: dict[str, Any],
    ) -> None:
        """根据 ML 训练结果生成并发布交易信号.

        Args:
            state: 当前任务状态（原地更新步骤状态）。
            symbol: 交易标的。
            train_result: _step_ml_train 返回的摘要字典。
        """
        from quantpilot.signals.broadcaster import SignalBroadcaster, TradingSignal

        step = self._get_step(state, "signal_gen")
        state.current_step = "signal_gen"
        step.status = "running"
        try:
            latest_signal: int = train_result.get("latest_class_signal", 0)
            latest_probs: dict[str, float] = train_result.get("latest_class_probabilities", {})

            # 将 -1/0/1 映射为 sell/hold/buy
            action_map = {-1: "sell", 0: "hold", 1: "buy"}
            action: str = action_map.get(latest_signal, "hold")

            # confidence：取对应 action 的概率，若无则默认 0.0
            action_key = str(latest_signal)
            confidence: float = float(latest_probs.get(action_key, 0.0))

            reversal_signal = train_result.get("reversal_signal", "none")
            market_regime = train_result.get("market_regime", "unknown")
            reason = (
                f"ML信号={action}，置信度={confidence:.2%}，"
                f"市场状态={market_regime}，反转信号={reversal_signal}"
            )

            signal = TradingSignal(
                source="autopilot_ml",
                symbol=symbol,
                action=action,
                price=0.0,  # 实时价格由下游获取，此处标记为 0
                confidence=confidence,
                reason=reason,
            )
            broadcaster = SignalBroadcaster()
            signal_id = await broadcaster.publish(signal)

            state.result["signal_action"] = action
            state.result["signal_confidence"] = confidence
            state.result["signal_published"] = True

            step.status = "done"
            step.message = f"信号已发布：{action}（置信度 {confidence:.2%}，id={signal_id}）"
            step.detail = {
                "action": action,
                "confidence": confidence,
                "signal_id": signal_id,
                "reason": reason,
            }
            logger.info(
                "[Pipeline] signal_gen: {} → action={} confidence={:.2%} id={}",
                symbol, action, confidence, signal_id,
            )
        except Exception as exc:
            step.status = "error"
            step.message = str(exc)
            state.result["signal_published"] = False
            raise
