"""加密研究服务：多周期数据集与 walk-forward 训练摘要."""

from __future__ import annotations

from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import pandas as pd
from loguru import logger

from quantpilot_common.data.models import OHLCVBar
from quantpilot_common.data.storage import MarketDataStorage
from quantpilot_quant.ml.crypto_features import CryptoFeaturePipeline
from quantpilot_quant.ml.ensemble import EnsembleStrategy
from quantpilot_quant.ml.feature_selector import FeatureSelector

# 支持 lgb.LGBMClassifier 和 EnsembleStrategy 的联合类型（duck typing）
_MulticlassModel = lgb.LGBMClassifier | EnsembleStrategy
from quantpilot_quant.optimize.engine import OptimizationEngine, ParamGrid
from quantpilot_quant.research.crypto_dataset import MultiTimeframeDatasetBuilder
from quantpilot_quant.research.models import (
    CryptoResearchDatasetSummary,
    CryptoResearchOptimizationSummary,
    CryptoResearchTrainSummary,
    WalkForwardWindowMetric,
)
from quantpilot_quant.research.storage import CryptoResearchStorage
from quantpilot_quant.research.validation import TimeSeriesValidationConfig, build_walk_forward_windows
from quantpilot_quant.strategy.templates.vwap_ema_trend import VWAPEMATrendStrategy


@dataclass(frozen=True, slots=True)
class CryptoResearchRequest:
    """研究请求参数."""

    symbol: str
    base_timeframe: str
    higher_timeframes: list[str]
    limit: int
    validation: TimeSeriesValidationConfig


class CryptoResearchService:
    """多时间维度 OKX 加密研究服务."""

    def __init__(
        self,
        storage: MarketDataStorage,
        corr_threshold: float = 0.85,
        use_ensemble: bool = False,
    ) -> None:
        self._storage = storage
        self._builder = MultiTimeframeDatasetBuilder(storage)
        self._pipeline = CryptoFeaturePipeline()
        self._results = CryptoResearchStorage()
        self._feature_selector = FeatureSelector(corr_threshold=corr_threshold)
        self._use_ensemble = use_ensemble

    def build_dataset_summary(
        self,
        *,
        symbol: str,
        base_timeframe: str,
        higher_timeframes: list[str],
        limit: int,
    ) -> CryptoResearchDatasetSummary:
        dataset = self._builder.build(
            symbol=symbol,
            base_timeframe=base_timeframe,
            higher_timeframes=higher_timeframes,
            limit=limit,
        )
        return CryptoResearchDatasetSummary(
            symbol=symbol,
            base_timeframe=base_timeframe,
            higher_timeframes=higher_timeframes,
            rows=dataset.rows,
            dataset_version=dataset.data_version,
            dataset_columns=list(dataset.frame.columns),
        )

    def train_and_validate(self, request: CryptoResearchRequest) -> CryptoResearchTrainSummary:
        dataset = self._builder.build(
            symbol=request.symbol,
            base_timeframe=request.base_timeframe,
            higher_timeframes=request.higher_timeframes,
            limit=request.limit,
        )
        features = self._pipeline.compute(dataset.frame)
        feature_columns = self._feature_columns(features)

        # ── 动态特征筛选：去除高相关冗余因子，保留互信息更高的特征 ──────────
        # 注意：此处在全量数据上执行筛选（全局筛选），特征列名一经确定后在所有
        # walk-forward 窗口中复用。如需消除轻微前视偏差，可改为在每个 window
        # 的 train_df 内分别调用 fit_transform，代价是每窗口耗时略增。
        if len(features) >= 10 and len(feature_columns) >= 2:
            try:
                feature_columns, _selection_report = self._feature_selector.fit_transform(
                    X=features[feature_columns],
                    y=features["target_class"],
                    target_type="classification",
                )
            except ValueError as exc:
                logger.warning(f"[FeatureSelector] 跳过特征筛选：{exc}")
        # ─────────────────────────────────────────────────────────────────────

        windows = build_walk_forward_windows(total_rows=len(features), config=request.validation)
        if not windows:
            raise ValueError("数据不足，无法构建 walk-forward 验证窗口")

        window_metrics: list[WalkForwardWindowMetric] = []
        final_multiclass: _MulticlassModel | None = None
        final_reversal: lgb.LGBMClassifier | None = None

        for window in windows:
            train_df = features.iloc[window.train_start : window.train_end + 1]
            test_df = features.iloc[window.test_start : window.test_end + 1]
            final_multiclass = self._fit_multiclass(train_df, feature_columns)
            y_true = test_df["target_class"].to_numpy()
            y_pred = self._predict_multiclass(final_multiclass, test_df, feature_columns)
            strategy_return = float((y_pred * test_df["forward_return_1d"].to_numpy()).mean())
            accuracy = float((y_true == y_pred).mean())
            window_metrics.append(
                WalkForwardWindowMetric(
                    train_start=window.train_start,
                    train_end=window.train_end,
                    test_start=window.test_start,
                    test_end=window.test_end,
                    accuracy=accuracy,
                    strategy_return=strategy_return,
                )
            )
            final_reversal = self._fit_reversal(train_df, feature_columns)

        assert final_multiclass is not None
        assert final_reversal is not None

        latest_probs = self._latest_probabilities(final_multiclass, features.tail(1), feature_columns)
        latest_signal = max(latest_probs, key=latest_probs.get)
        reversal_probability = float(final_reversal.predict_proba(features[feature_columns].tail(1))[0][1])
        importances = self._feature_importance(final_multiclass, feature_columns)
        evidence = [name for name, _ in sorted(importances.items(), key=lambda item: item[1], reverse=True)[:3]]

        summary = CryptoResearchTrainSummary(
            symbol=request.symbol,
            base_timeframe=request.base_timeframe,
            higher_timeframes=request.higher_timeframes,
            rows=len(features),
            dataset_version=dataset.data_version,
            feature_count=len(feature_columns),
            feature_columns=feature_columns,
            validation_windows=len(window_metrics),
            window_metrics=window_metrics,
            mean_accuracy=float(np.mean([item.accuracy for item in window_metrics])),
            mean_strategy_return=float(np.mean([item.strategy_return for item in window_metrics])),
            latest_class_signal=int(latest_signal),
            latest_class_probabilities=latest_probs,
            feature_importance=importances,
            reversal_probability=reversal_probability,
            reversal_signal="watch_reversal" if reversal_probability >= 0.5 else "none",
            reversal_evidence=evidence,
            market_regime=self._market_regime(features),
            recommended_strategy_ids=["vwap_ema_trend"],
            recommended_timeframes=["15m", "1h"],
            parameter_search_ready=True,
        )
        self._results.save_latest(summary)
        return summary

    def get_latest(self, *, symbol: str, base_timeframe: str) -> CryptoResearchTrainSummary | None:
        """读取最新缓存结果."""
        return self._results.load_latest(symbol=symbol, base_timeframe=base_timeframe)

    def optimize_strategy(
        self,
        *,
        symbol: str,
        base_timeframe: str,
        higher_timeframes: list[str],
        limit: int,
        param_grid: dict[str, list[int | float]],
    ) -> CryptoResearchOptimizationSummary:
        """对 VWAP_EMA_Trend 策略运行参数搜索."""
        bars_frame = self._storage.query_bars(symbol=symbol, timeframe=base_timeframe, limit=limit).to_pandas()
        if bars_frame.empty:
            raise ValueError("无可用 bar 数据用于参数搜索")
        bars_for_backtest = [
            OHLCVBar(
                symbol=symbol,
                timeframe=base_timeframe,
                timestamp=row["timestamp"].to_pydatetime() if hasattr(row["timestamp"], "to_pydatetime") else row["timestamp"],
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
                turnover=None if pd.isna(row.get("turnover")) else row.get("turnover"),
            )
            for row in bars_frame.to_dict(orient="records")
        ]

        from quantpilot_quant.backtest.engine import BacktestConfig

        engine = OptimizationEngine(
            BacktestConfig(symbol=symbol, timeframe=base_timeframe, initial_cash=10_000.0),
            bars_for_backtest,
        )
        results = engine.grid_search(VWAPEMATrendStrategy, ParamGrid(param_grid))
        if not results:
            raise ValueError("参数搜索未返回有效结果")

        windows = build_walk_forward_windows(
            total_rows=len(bars_for_backtest),
            config=TimeSeriesValidationConfig(train_size=60, test_size=20, step_size=20, embargo_size=2),
        )
        window_metrics = [
            WalkForwardWindowMetric(
                train_start=window.train_start,
                train_end=window.train_end,
                test_start=window.test_start,
                test_end=window.test_end,
                accuracy=0.0,
                strategy_return=result.total_return,
            )
            for window, result in zip(windows, results[: min(len(windows), len(results))], strict=False)
        ]
        best = results[0]
        summary = CryptoResearchOptimizationSummary(
            symbol=symbol,
            strategy_id="vwap_ema_trend",
            base_timeframe=base_timeframe,
            higher_timeframes=higher_timeframes,
            best_params=best.params,
            window_count=len(windows),
            mean_accuracy=0.0,
            mean_strategy_return=best.total_return,
            max_drawdown=best.max_drawdown,
            window_metrics=window_metrics,
        )
        self._results.save_latest_optimization(summary)
        return summary

    def _feature_columns(self, features: pd.DataFrame) -> list[str]:
        excluded = {"target_class", "target_reversal", "forward_return_1d"}
        return [column for column in features.columns if column not in excluded and pd.api.types.is_numeric_dtype(features[column])]

    def _fit_multiclass(self, df: pd.DataFrame, feature_columns: list[str]) -> _MulticlassModel:
        """训练多分类模型.

        ``use_ensemble=True`` 时返回 ``EnsembleStrategy``（LightGBM + CatBoost 融合）；
        否则返回标准 ``lgb.LGBMClassifier``。两者均支持 ``predict_proba()``，
        后续方法通过 duck typing 统一调用。
        """
        if self._use_ensemble:
            ens = EnsembleStrategy(
                lgbm_params={
                    "n_estimators": 60, "num_leaves": 31,
                    "learning_rate": 0.05, "n_jobs": 1, "verbosity": -1,
                },
                catboost_params={
                    "iterations": 100, "depth": 4,
                    "learning_rate": 0.05, "thread_count": 1,
                },
            )
            # EnsembleStrategy 要求目标列名为 "target"，从 "target_class" 重命名
            train_df = df.assign(target=df["target_class"])
            ens.fit(train_df, feature_columns=feature_columns)
            return ens

        model = lgb.LGBMClassifier(
            objective="multiclass",
            num_class=3,
            n_estimators=60,
            learning_rate=0.05,
            num_leaves=31,
            n_jobs=1,
            random_state=42,
            verbosity=-1,
        )
        model.fit(df[feature_columns], (df["target_class"] + 1).to_numpy())
        return model

    def _fit_reversal(self, df: pd.DataFrame, feature_columns: list[str]) -> lgb.LGBMClassifier:
        model = lgb.LGBMClassifier(
            objective="binary",
            n_estimators=40,
            learning_rate=0.05,
            num_leaves=15,
            n_jobs=1,
            random_state=42,
            verbosity=-1,
        )
        model.fit(df[feature_columns], df["target_reversal"].to_numpy())
        return model

    def _predict_multiclass(
        self,
        model: _MulticlassModel,
        df: pd.DataFrame,
        feature_columns: list[str],
    ) -> np.ndarray:
        if isinstance(model, EnsembleStrategy):
            # EnsembleStrategy.predict() 返回 list[int]，已是 -1/0/1
            return np.array(model.predict(df[feature_columns]))
        # lgb.LGBMClassifier.predict() 返回 0/1/2，需减 1
        return model.predict(df[feature_columns]) - 1  # type: ignore[operator]

    def _latest_probabilities(
        self,
        model: _MulticlassModel,
        df: pd.DataFrame,
        feature_columns: list[str],
    ) -> dict[str, float]:
        # 两种模型均实现了 predict_proba(df) → shape (n, 3)
        probs = model.predict_proba(df[feature_columns])[0]  # type: ignore[union-attr]
        return {
            "-1": float(probs[0]),
            "0": float(probs[1]),
            "1": float(probs[2]),
        }

    def _feature_importance(
        self,
        model: _MulticlassModel,
        feature_columns: list[str],
    ) -> dict[str, float]:
        if isinstance(model, EnsembleStrategy):
            # 按模型权重加权平均 LGBM 和 CatBoost 的重要度
            imps = model.feature_importances()
            w_lgbm, w_cb = model.weights
            combined = {
                f: w_lgbm * imps["lgbm"].get(f, 0.0) + w_cb * imps["catboost"].get(f, 0.0)
                for f in feature_columns
            }
            total = sum(combined.values()) or 1.0
            return {f: v / total for f, v in combined.items()}

        values = model.feature_importances_  # type: ignore[union-attr]
        total = float(values.sum()) or 1.0
        return {feature: float(score / total) for feature, score in zip(feature_columns, values, strict=False)}

    def _market_regime(self, features: pd.DataFrame) -> str:
        latest = features.iloc[-1]
        if latest["adx_14"] >= 25 and latest["ema_spread_10_20"] > 0:
            return "trend"
        if latest["atr_14"] > features["atr_14"].quantile(0.75):
            return "high_volatility"
        return "range"

    def get_latest_optimization(
        self,
        *,
        symbol: str,
        base_timeframe: str,
        strategy_id: str,
    ) -> CryptoResearchOptimizationSummary | None:
        """读取最新缓存的优化结果."""
        return self._results.load_latest_optimization(
            symbol=symbol,
            base_timeframe=base_timeframe,
            strategy_id=strategy_id,
        )
