"""LightGBM 策略 — 基于 ML 模型产生交易信号."""
from __future__ import annotations

import pandas as pd
from loguru import logger


class LGBMStrategy:
    """LightGBM 分类器策略，预测未来价格方向."""

    FEATURE_COLS = [
        "returns", "log_returns", "momentum", "momentum_10",
        "volatility", "volatility_20", "ma5_ratio", "ma20_ratio",
        "volume_ratio", "hl_ratio", "oc_ratio",
    ]

    def __init__(self) -> None:
        self._model: object | None = None

    def fit(self, df: pd.DataFrame) -> None:
        """训练 LightGBM 分类器."""
        import lightgbm as lgb

        if "target" not in df.columns:
            raise ValueError("df 缺少 'target' 列")

        available_features = [c for c in self.FEATURE_COLS if c in df.columns]
        X = df[available_features].values
        y = df["target"].values

        # 将 -1/0/1 映射为 0/1/2（LightGBM 多分类）
        y_mapped = y + 1

        params = {
            "objective": "multiclass",
            "num_class": 3,
            "n_estimators": 50,
            "learning_rate": 0.1,
            "num_leaves": 15,
            "verbosity": -1,
        }
        clf = lgb.LGBMClassifier(**params)
        clf.fit(X, y_mapped)
        self._model = clf
        logger.info(f"[ML] LGBMStrategy 训练完成，样本数={len(X)}, 特征数={len(available_features)}")

    def predict(self, df: pd.DataFrame) -> list[int]:
        """对新 K 线数据预测信号."""
        if self._model is None:
            raise RuntimeError("未训练: 请先调用 fit()")

        available_features = [c for c in self.FEATURE_COLS if c in df.columns]
        X = df[available_features].values
        raw = self._model.predict(X)  # type: ignore[union-attr]
        # 将 0/1/2 映射回 -1/0/1
        return [int(p) - 1 for p in raw]
