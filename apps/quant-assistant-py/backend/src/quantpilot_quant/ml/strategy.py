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
        self._fitted_features: list[str] | None = None  # 训练时实际使用的特征列名

    def fit(self, df: pd.DataFrame, feature_columns: list[str] | None = None) -> None:
        """训练 LightGBM 分类器.

        Parameters
        ----------
        df:
            含特征列和 "target" 列的 DataFrame。
        feature_columns:
            指定使用的特征列名列表。若为 ``None`` 则使用 ``FEATURE_COLS`` 中
            在 ``df`` 内存在的列。传入 ``FeatureSelector.fit_transform()`` 的
            筛选结果可直接赋给此参数，跳过冗余特征。
        """
        import lightgbm as lgb

        if "target" not in df.columns:
            raise ValueError("df 缺少 'target' 列")

        cols = feature_columns if feature_columns is not None else self.FEATURE_COLS
        available_features = [c for c in cols if c in df.columns]
        self._fitted_features = available_features  # 存储供 predict 复用
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
        """对新 K 线数据预测信号.

        自动使用 ``fit()`` 时实际选用的特征列；
        若模型尚未训练（``_fitted_features`` 为 None），则回退到 ``FEATURE_COLS``。
        """
        if self._model is None:
            raise RuntimeError("未训练: 请先调用 fit()")

        cols = self._fitted_features if self._fitted_features is not None else self.FEATURE_COLS
        available_features = [c for c in cols if c in df.columns]
        X = df[available_features].values
        raw = self._model.predict(X)  # type: ignore[union-attr]
        # 将 0/1/2 映射回 -1/0/1
        return [int(p) - 1 for p in raw]

    def predict_proba(self, df: pd.DataFrame) -> "np.ndarray":
        """返回各类别概率矩阵，shape ``(n, 3)``，列对应信号 ``[-1, 0, 1]``.

        与 ``EnsembleStrategy.predict_proba`` 保持相同签名，两个模型可多态互换。
        """
        import numpy as np  # noqa: F401

        if self._model is None:
            raise RuntimeError("未训练: 请先调用 fit()")

        cols = self._fitted_features if self._fitted_features is not None else self.FEATURE_COLS
        available_features = [c for c in cols if c in df.columns]
        X = df[available_features].values
        return self._model.predict_proba(X)  # type: ignore[union-attr]
