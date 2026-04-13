"""加密研究服务：多周期数据集与 walk-forward 训练摘要."""

from __future__ import annotations

from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import pandas as pd

from quantpilot.data.storage import MarketDataStorage
from quantpilot.ml.crypto_features import CryptoFeaturePipeline
from quantpilot.research.crypto_dataset import MultiTimeframeDatasetBuilder
from quantpilot.research.models import (
    CryptoResearchDatasetSummary,
    CryptoResearchTrainSummary,
    WalkForwardWindowMetric,
)
from quantpilot.research.validation import TimeSeriesValidationConfig, build_walk_forward_windows


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

    def __init__(self, storage: MarketDataStorage) -> None:
        self._storage = storage
        self._builder = MultiTimeframeDatasetBuilder(storage)
        self._pipeline = CryptoFeaturePipeline()

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
        windows = build_walk_forward_windows(total_rows=len(features), config=request.validation)
        if not windows:
            raise ValueError("数据不足，无法构建 walk-forward 验证窗口")

        window_metrics: list[WalkForwardWindowMetric] = []
        final_multiclass: lgb.LGBMClassifier | None = None
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

        return CryptoResearchTrainSummary(
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
        )

    def _feature_columns(self, features: pd.DataFrame) -> list[str]:
        excluded = {"target_class", "target_reversal", "forward_return_1d"}
        return [column for column in features.columns if column not in excluded and pd.api.types.is_numeric_dtype(features[column])]

    def _fit_multiclass(self, df: pd.DataFrame, feature_columns: list[str]) -> lgb.LGBMClassifier:
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
        model: lgb.LGBMClassifier,
        df: pd.DataFrame,
        feature_columns: list[str],
    ) -> np.ndarray:
        return model.predict(df[feature_columns]) - 1

    def _latest_probabilities(
        self,
        model: lgb.LGBMClassifier,
        df: pd.DataFrame,
        feature_columns: list[str],
    ) -> dict[str, float]:
        probs = model.predict_proba(df[feature_columns])[0]
        return {
            "-1": float(probs[0]),
            "0": float(probs[1]),
            "1": float(probs[2]),
        }

    def _feature_importance(
        self,
        model: lgb.LGBMClassifier,
        feature_columns: list[str],
    ) -> dict[str, float]:
        values = model.feature_importances_
        total = float(values.sum()) or 1.0
        return {feature: float(score / total) for feature, score in zip(feature_columns, values, strict=False)}
