"""EnsembleStrategy 单元测试 — LightGBM + CatBoost 加权融合."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quantpilot.ml.ensemble import EnsembleStrategy


# ── 测试数据工厂 ───────────────────────────────────────────────────────────────


def make_df(n: int = 100, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    cols = EnsembleStrategy.FEATURE_COLS
    data = {c: rng.normal(0, 1, n) for c in cols}
    data["target"] = rng.choice([-1, 0, 1], n)
    return pd.DataFrame(data)


# ── 基本 fit / predict ─────────────────────────────────────────────────────────


class TestBasicFitPredict:
    def test_predict_returns_valid_signals(self) -> None:
        ens = EnsembleStrategy()
        ens.fit(make_df(100))
        sigs = ens.predict(make_df(20, seed=99))
        assert len(sigs) == 20
        assert all(s in (-1, 0, 1) for s in sigs)

    def test_predict_proba_shape(self) -> None:
        ens = EnsembleStrategy()
        ens.fit(make_df(100))
        proba = ens.predict_proba(make_df(30, seed=2))
        assert proba.shape == (30, 3)

    def test_predict_proba_sums_to_one(self) -> None:
        ens = EnsembleStrategy()
        ens.fit(make_df(100))
        proba = ens.predict_proba(make_df(40, seed=3))
        assert np.allclose(proba.sum(axis=1), 1.0, atol=1e-6)

    def test_predict_consistent_with_proba(self) -> None:
        """predict() 应等于 argmax(predict_proba()) - 1."""
        ens = EnsembleStrategy()
        ens.fit(make_df(100))
        test = make_df(20, seed=5)
        sigs = ens.predict(test)
        proba = ens.predict_proba(test)
        expected = [int(np.argmax(proba[i])) - 1 for i in range(len(sigs))]
        assert sigs == expected


# ── 权重 ──────────────────────────────────────────────────────────────────────


class TestWeights:
    def test_default_weights(self) -> None:
        ens = EnsembleStrategy()
        assert abs(ens.weights[0] - 0.4) < 1e-9
        assert abs(ens.weights[1] - 0.6) < 1e-9

    def test_weights_normalize(self) -> None:
        ens = EnsembleStrategy(lgbm_weight=2.0, catboost_weight=8.0)
        assert abs(ens.weights[0] - 0.2) < 1e-9
        assert abs(ens.weights[1] - 0.8) < 1e-9
        assert abs(sum(ens.weights) - 1.0) < 1e-9

    def test_equal_weights(self) -> None:
        ens = EnsembleStrategy(lgbm_weight=1.0, catboost_weight=1.0)
        assert abs(ens.weights[0] - 0.5) < 1e-9
        assert abs(ens.weights[1] - 0.5) < 1e-9

    def test_invalid_weights_raises(self) -> None:
        with pytest.raises(ValueError):
            EnsembleStrategy(lgbm_weight=0.0, catboost_weight=1.0)
        with pytest.raises(ValueError):
            EnsembleStrategy(lgbm_weight=-0.1, catboost_weight=0.9)


# ── RobustScaler 窗口隔离 ──────────────────────────────────────────────────────


class TestScalerIsolation:
    def test_different_train_data_different_scaler(self) -> None:
        """两次独立 fit 产生不同的 scaler 统计量（防止全局污染）."""
        ens1 = EnsembleStrategy()
        ens2 = EnsembleStrategy()
        ens1.fit(make_df(100, seed=1))
        ens2.fit(make_df(100, seed=2))
        # 不同随机种子 → 不同均值/中位数
        assert not np.allclose(ens1._scaler.center_, ens2._scaler.center_)

    def test_refit_updates_scaler(self) -> None:
        """同一实例重新 fit 后 scaler 统计量应更新."""
        ens = EnsembleStrategy()
        ens.fit(make_df(100, seed=1))
        center_before = ens._scaler.center_.copy()
        ens.fit(make_df(100, seed=99))
        assert not np.allclose(center_before, ens._scaler.center_)

    def test_scaler_fitted_inside_fit(self) -> None:
        """fit() 调用后 scaler 应已训练."""
        ens = EnsembleStrategy()
        assert ens._scaler is None
        ens.fit(make_df(100))
        assert ens._scaler is not None


# ── 特征列控制 ────────────────────────────────────────────────────────────────


class TestFeatureColumns:
    def test_feature_columns_override(self) -> None:
        ens = EnsembleStrategy()
        subset = EnsembleStrategy.FEATURE_COLS[:4]
        ens.fit(make_df(100), feature_columns=subset)
        assert ens.fitted_features == subset

    def test_fitted_features_stored(self) -> None:
        ens = EnsembleStrategy()
        ens.fit(make_df(100))
        assert ens.fitted_features is not None
        assert len(ens.fitted_features) == len(EnsembleStrategy.FEATURE_COLS)

    def test_predict_uses_fitted_features(self) -> None:
        ens = EnsembleStrategy()
        subset = EnsembleStrategy.FEATURE_COLS[:3]
        ens.fit(make_df(100), feature_columns=subset)
        test = make_df(20, seed=7)
        sigs = ens.predict(test)  # 应用 fitted_features，不会崩溃
        assert len(sigs) == 20


# ── 错误处理 ──────────────────────────────────────────────────────────────────


class TestErrorHandling:
    def test_predict_before_fit_raises(self) -> None:
        ens = EnsembleStrategy()
        with pytest.raises(RuntimeError, match="未训练"):
            ens.predict(make_df(10))

    def test_predict_proba_before_fit_raises(self) -> None:
        ens = EnsembleStrategy()
        with pytest.raises(RuntimeError, match="未训练"):
            ens.predict_proba(make_df(10))

    def test_feature_importances_before_fit_raises(self) -> None:
        ens = EnsembleStrategy()
        with pytest.raises(RuntimeError, match="未训练"):
            ens.feature_importances()

    def test_missing_target_column_raises(self) -> None:
        ens = EnsembleStrategy()
        df = make_df(100).drop(columns=["target"])
        with pytest.raises(ValueError, match="target"):
            ens.fit(df)

    def test_no_available_features_raises(self) -> None:
        ens = EnsembleStrategy()
        df = make_df(100)
        with pytest.raises(ValueError):
            ens.fit(df, feature_columns=["nonexistent_col"])


# ── 特征重要度 ────────────────────────────────────────────────────────────────


class TestFeatureImportances:
    def test_importances_keys(self) -> None:
        ens = EnsembleStrategy()
        ens.fit(make_df(100))
        imps = ens.feature_importances()
        assert "lgbm" in imps
        assert "catboost" in imps

    def test_lgbm_importances_normalized(self) -> None:
        ens = EnsembleStrategy()
        ens.fit(make_df(100))
        imps = ens.feature_importances()
        assert abs(sum(imps["lgbm"].values()) - 1.0) < 1e-6

    def test_catboost_importances_normalized(self) -> None:
        ens = EnsembleStrategy()
        ens.fit(make_df(100))
        imps = ens.feature_importances()
        assert abs(sum(imps["catboost"].values()) - 1.0) < 1e-6

    def test_importances_feature_names_match(self) -> None:
        ens = EnsembleStrategy()
        ens.fit(make_df(100))
        imps = ens.feature_importances()
        assert set(imps["lgbm"].keys()) == set(EnsembleStrategy.FEATURE_COLS)


# ── 自定义超参数 ───────────────────────────────────────────────────────────────


class TestCustomParams:
    def test_custom_lgbm_params(self) -> None:
        ens = EnsembleStrategy(lgbm_params={"n_estimators": 5})
        ens.fit(make_df(100))
        sigs = ens.predict(make_df(10))
        assert all(s in (-1, 0, 1) for s in sigs)

    def test_custom_catboost_params(self) -> None:
        ens = EnsembleStrategy(catboost_params={"iterations": 5})
        ens.fit(make_df(100))
        sigs = ens.predict(make_df(10))
        assert all(s in (-1, 0, 1) for s in sigs)
