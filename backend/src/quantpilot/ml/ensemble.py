"""异构集成策略 — LightGBM + CatBoost 加权融合.

设计原则
--------
1. **接口兼容**：与 ``LGBMStrategy`` 保持相同的 ``fit`` / ``predict`` 签名，
   可在任何已调用 ``LGBMStrategy`` 的地方直接替换。
2. **加权融合**：对两个模型的 ``predict_proba``（shape ``[n, 3]``，类别 0/1/2
   对应信号 -1/0/1）按可配置权重加权求和，取 argmax 得到最终预测类别。
3. **RobustScaler 窗口独立**：Scaler 在每次 ``fit()`` 调用内部 ``fit_transform``，
   保证每个滚动窗口只使用本窗口训练数据的统计量，完全避免未来信息泄露。
   注意：LightGBM / CatBoost 均为树模型，理论上对单调变换不敏感；
   此处应用 Scaler 的主要目的是确保 pipeline 口径统一，
   以及在未来扩展线性基学习器时开箱即用。
4. **延迟导入**：``lightgbm`` 和 ``catboost`` 均在方法内部导入，
   未安装时给出明确错误信息，不影响其他模块正常导入。

调用示例
--------
::

    ensemble = EnsembleStrategy(lgbm_weight=0.4, catboost_weight=0.6)
    ensemble.fit(train_df, feature_columns=selected_cols)
    signals: list[int] = ensemble.predict(test_df)           # -1 / 0 / 1
    proba: np.ndarray  = ensemble.predict_proba(test_df)     # shape (n, 3)
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.preprocessing import RobustScaler


class EnsembleStrategy:
    """LightGBM + CatBoost 异构集成策略.

    Parameters
    ----------
    lgbm_weight:
        LightGBM 模型的融合权重（默认 0.4）。
        与 ``catboost_weight`` 之和无需等于 1，内部自动归一化。
    catboost_weight:
        CatBoost 模型的融合权重（默认 0.6）。
    lgbm_params:
        传给 ``lgb.LGBMClassifier`` 的额外超参数，会与默认值合并。
    catboost_params:
        传给 ``CatBoostClassifier`` 的额外超参数，会与默认值合并。
    """

    # 沿用 LGBMStrategy 的默认特征列，可被 fit(feature_columns=...) 覆盖
    FEATURE_COLS: list[str] = [
        "returns", "log_returns", "momentum", "momentum_10",
        "volatility", "volatility_20", "ma5_ratio", "ma20_ratio",
        "volume_ratio", "hl_ratio", "oc_ratio",
    ]

    def __init__(
        self,
        lgbm_weight: float = 0.4,
        catboost_weight: float = 0.6,
        lgbm_params: dict[str, Any] | None = None,
        catboost_params: dict[str, Any] | None = None,
    ) -> None:
        if lgbm_weight <= 0 or catboost_weight <= 0:
            raise ValueError("lgbm_weight 和 catboost_weight 均须 > 0")
        total = lgbm_weight + catboost_weight
        self._w_lgbm = lgbm_weight / total
        self._w_catboost = catboost_weight / total

        self._lgbm_params: dict[str, Any] = lgbm_params or {}
        self._catboost_params: dict[str, Any] = catboost_params or {}

        # 训练后填充
        self._scaler: RobustScaler | None = None
        self._lgbm: object | None = None
        self._catboost: object | None = None
        self._fitted_features: list[str] | None = None

    # ── 主接口 ────────────────────────────────────────────────────────────────

    def fit(
        self,
        df: pd.DataFrame,
        feature_columns: list[str] | None = None,
    ) -> None:
        """训练集成模型.

        Parameters
        ----------
        df:
            含特征列和 ``"target"`` 列（值域 ``{-1, 0, 1}``）的 DataFrame。
        feature_columns:
            指定使用的特征列名列表。为 ``None`` 时使用 ``FEATURE_COLS`` 中
            在 ``df`` 内存在的列。传入 ``FeatureSelector.fit_transform()``
            的筛选结果可直接赋给此参数。

        Notes
        -----
        ``RobustScaler`` 在本次 ``fit()`` 调用内独立 ``fit_transform``，
        统计量仅来自当前传入的 ``df``，不跨窗口共享，彻底隔绝未来信息。
        """
        try:
            import lightgbm as lgb
        except ImportError as e:
            raise ImportError("请先安装 lightgbm: uv add lightgbm>=4.0.0") from e
        try:
            from catboost import CatBoostClassifier
        except ImportError as e:
            raise ImportError("请先安装 catboost: uv add catboost>=1.2.0") from e

        if "target" not in df.columns:
            raise ValueError("df 缺少 'target' 列（值域应为 -1 / 0 / 1）")

        cols = feature_columns if feature_columns is not None else self.FEATURE_COLS
        available = [c for c in cols if c in df.columns]
        if not available:
            raise ValueError(f"df 中找不到任何指定特征列：{cols}")

        self._fitted_features = available
        X_raw = df[available]                        # 保留列名，供 LightGBM 特征名追踪
        y = (df["target"].values + 1).astype(int)  # {-1,0,1} → {0,1,2}

        # ── RobustScaler：仅在本窗口训练数据上 fit ────────────────────────
        self._scaler = RobustScaler()
        X_scaled = self._scaler.fit_transform(X_raw)
        X = pd.DataFrame(X_scaled, columns=available)  # 还原列名，消除 LightGBM 特征名警告

        # ── LightGBM ──────────────────────────────────────────────────────
        lgbm_defaults: dict[str, Any] = {
            "objective": "multiclass",
            "num_class": 3,
            "n_estimators": 50,
            "learning_rate": 0.1,
            "num_leaves": 15,
            "n_jobs": 1,
            "random_state": 42,
            "verbosity": -1,
        }
        lgbm_cfg = {**lgbm_defaults, **self._lgbm_params}
        self._lgbm = lgb.LGBMClassifier(**lgbm_cfg)
        self._lgbm.fit(X, y)  # type: ignore[union-attr]

        # ── CatBoost ──────────────────────────────────────────────────────
        catboost_defaults: dict[str, Any] = {
            "iterations": 100,
            "learning_rate": 0.1,
            "depth": 4,
            "loss_function": "MultiClass",
            "classes_count": 3,
            "random_seed": 42,
            "verbose": 0,
            "task_type": "CPU",
            "thread_count": 1,
        }
        catboost_cfg = {**catboost_defaults, **self._catboost_params}
        self._catboost = CatBoostClassifier(**catboost_cfg)
        self._catboost.fit(X, y)  # type: ignore[union-attr]

        logger.info(
            "[Ensemble] 训练完成 | 样本={} 特征={} "
            "lgbm_weight={:.2f} catboost_weight={:.2f}",
            len(X), len(available), self._w_lgbm, self._w_catboost,
        )

    def predict(self, df: pd.DataFrame) -> list[int]:
        """预测信号（-1 / 0 / 1）.

        自动使用 ``fit()`` 时确定的特征列和 Scaler；
        若模型尚未训练则抛出 ``RuntimeError``。
        """
        proba = self.predict_proba(df)               # shape (n, 3)
        classes = np.argmax(proba, axis=1)           # 0/1/2
        return [int(c) - 1 for c in classes]        # → -1/0/1

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        """返回加权融合后的类别概率矩阵.

        Parameters
        ----------
        df:
            含特征列的 DataFrame（无需包含 target 列）。

        Returns
        -------
        np.ndarray
            shape ``(n_samples, 3)``，列对应信号 ``[-1, 0, 1]``。
            各行概率之和为 1.0。

        Raises
        ------
        RuntimeError
            模型尚未训练（未调用 ``fit()``）。
        """
        self._check_fitted()
        assert self._scaler is not None
        assert self._lgbm is not None
        assert self._catboost is not None
        assert self._fitted_features is not None

        available = [c for c in self._fitted_features if c in df.columns]
        X_scaled = self._scaler.transform(df[available])  # 用训练时的 Scaler 统计量变换
        X = pd.DataFrame(X_scaled, columns=available)     # 保持列名一致，避免特征名警告

        proba_lgbm: np.ndarray = self._lgbm.predict_proba(X)       # type: ignore[union-attr]
        proba_cb: np.ndarray   = self._catboost.predict_proba(X)    # type: ignore[union-attr]

        blended: np.ndarray = self._w_lgbm * proba_lgbm + self._w_catboost * proba_cb
        return blended

    # ── 辅助属性 ──────────────────────────────────────────────────────────────

    @property
    def fitted_features(self) -> list[str] | None:
        """训练时实际使用的特征列名（未训练时为 None）."""
        return self._fitted_features

    @property
    def weights(self) -> tuple[float, float]:
        """归一化后的 (lgbm_weight, catboost_weight) 元组."""
        return self._w_lgbm, self._w_catboost

    def feature_importances(self) -> dict[str, dict[str, float]]:
        """返回两个子模型各自的特征重要度（归一化到 [0, 1]）.

        Returns
        -------
        dict with keys ``"lgbm"`` and ``"catboost"``,
        each mapping feature_name → normalized_importance.
        """
        self._check_fitted()
        assert self._fitted_features is not None

        result: dict[str, dict[str, float]] = {}

        lgbm_imp: np.ndarray = self._lgbm.feature_importances_  # type: ignore[union-attr]
        lgbm_total = float(lgbm_imp.sum()) or 1.0
        result["lgbm"] = {
            f: float(v / lgbm_total)
            for f, v in zip(self._fitted_features, lgbm_imp, strict=False)
        }

        try:
            cb_imp: np.ndarray = self._catboost.get_feature_importance()  # type: ignore[union-attr]
        except Exception:
            # 兼容旧版本或异常状态：回退到 feature_importances_ 属性
            cb_imp = getattr(self._catboost, "feature_importances_", None)
            if cb_imp is None:
                cb_imp = np.ones(len(self._fitted_features))
        cb_total = float(cb_imp.sum()) or 1.0
        result["catboost"] = {
            f: float(v / cb_total)
            for f, v in zip(self._fitted_features, cb_imp, strict=False)
        }

        return result

    # ── 私有方法 ──────────────────────────────────────────────────────────────

    def _check_fitted(self) -> None:
        if self._lgbm is None or self._catboost is None or self._scaler is None:
            raise RuntimeError("未训练：请先调用 fit()")
