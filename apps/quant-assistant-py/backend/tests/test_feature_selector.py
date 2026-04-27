"""FeatureSelector 单元测试 — 皮尔逊去冗余 + 互信息排序."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quantpilot_quant.ml.feature_selector import FeatureSelector, SelectionReport


# ── 测试用数据工厂 ─────────────────────────────────────────────────────────────


def make_correlated(n: int = 100, seed: int = 42) -> tuple[pd.DataFrame, pd.Series]:
    """生成含高相关特征对的数据集.

    x1: 独立随机
    x2: 0.95 * x1 + 噪声  → 与 x1 高度相关（r ≈ 0.95）
    x3: 独立随机
    target: sign(x1 + x3)
    """
    rng = np.random.default_rng(seed)
    x1 = rng.normal(0, 1, n)
    x2 = 0.95 * x1 + 0.1 * rng.normal(0, 1, n)
    x3 = rng.normal(0, 1, n)
    y = np.sign(x1 + x3 + 0.05 * rng.normal(0, 1, n)).astype(int)
    return pd.DataFrame({"x1": x1, "x2": x2, "x3": x3}), pd.Series(y, name="target")


def make_independent(n: int = 100, seed: int = 0) -> tuple[pd.DataFrame, pd.Series]:
    """生成三个相互独立的特征（无高相关对）."""
    rng = np.random.default_rng(seed)
    X = pd.DataFrame({c: rng.normal(0, 1, n) for c in ["a", "b", "c"]})
    y = pd.Series(rng.choice([-1, 0, 1], n), name="target")
    return X, y


# ── 核心去冗余逻辑 ─────────────────────────────────────────────────────────────


class TestGreedyDeduplication:
    def test_removes_correlated_feature(self) -> None:
        X, y = make_correlated()
        sel = FeatureSelector(corr_threshold=0.85)
        selected, report = sel.fit_transform(X, y)
        # x2 与 x1 相关性 ~0.95 > 0.85，其中一个应被移除
        assert not ("x1" in selected and "x2" in selected), "高相关对 x1/x2 不应同时保留"

    def test_keeps_independent_feature(self) -> None:
        X, y = make_correlated()
        sel = FeatureSelector(corr_threshold=0.85)
        selected, _ = sel.fit_transform(X, y)
        assert "x3" in selected, "独立特征 x3 不应被移除"

    def test_keeps_higher_mi_of_correlated_pair(self) -> None:
        """在相关对中，保留与目标互信息更高的特征."""
        X, y = make_correlated()
        sel = FeatureSelector(corr_threshold=0.85)
        selected, report = sel.fit_transform(X, y)
        # x1 比 x2 与 target 相关性更强（x2 是 x1 + 噪声），应保留 x1
        if "x1" not in selected and "x2" in selected:
            # 如果保留了 x2，则 x2 的 MI 必须 >= x1 的 MI
            assert report.mi_scores.get("x2", 0) >= report.mi_scores.get("x1", 0)

    def test_high_threshold_keeps_all(self) -> None:
        X, y = make_independent()
        sel = FeatureSelector(corr_threshold=0.999)  # 极高阈值
        selected, report = sel.fit_transform(X, y)
        # 独立特征之间相关性 << 0.999，全部保留
        assert len(selected) == 3
        assert report.n_selected == 3


# ── SelectionReport 完整性 ────────────────────────────────────────────────────


class TestSelectionReport:
    def test_report_fields_complete(self) -> None:
        X, y = make_correlated()
        sel = FeatureSelector(corr_threshold=0.85)
        selected, report = sel.fit_transform(X, y)

        assert isinstance(report, SelectionReport)
        assert report.n_original == 3
        assert report.n_selected == len(selected)
        assert len(report.selected_features) == len(selected)
        assert len(report.removed_features) == report.n_original - report.n_selected
        assert report.corr_threshold == 0.85

    def test_mi_scores_normalized(self) -> None:
        X, y = make_correlated()
        sel = FeatureSelector()
        _, report = sel.fit_transform(X, y)
        scores = list(report.mi_scores.values())
        assert max(scores) <= 1.0 + 1e-9
        assert min(scores) >= 0.0 - 1e-9
        assert abs(max(scores) - 1.0) < 1e-6, "最高 MI 特征应归一化为 1.0"

    def test_removal_reasons_populated(self) -> None:
        X, y = make_correlated()
        sel = FeatureSelector(corr_threshold=0.85)
        _, report = sel.fit_transform(X, y)
        for removed in report.removed_features:
            assert removed in report.removal_reasons, f"{removed} 应有移除原因"

    def test_corr_matrix_shape(self) -> None:
        X, y = make_correlated()
        sel = FeatureSelector()
        _, report = sel.fit_transform(X, y)
        assert report.corr_matrix.shape == (3, 3)
        # 对角线为 1
        assert all(abs(report.corr_matrix.iloc[i, i] - 1.0) < 1e-9 for i in range(3))


# ── 输入边界检查 ───────────────────────────────────────────────────────────────


class TestInputValidation:
    def test_empty_dataframe_raises(self) -> None:
        sel = FeatureSelector()
        with pytest.raises(ValueError, match="空|empty"):
            sel.fit_transform(pd.DataFrame(), pd.Series(dtype=float))

    def test_too_few_rows_raises(self) -> None:
        X = pd.DataFrame({"a": range(5), "b": range(5)})
        y = pd.Series([0, 1, -1, 0, 1])
        sel = FeatureSelector()
        with pytest.raises(ValueError, match="10"):
            sel.fit_transform(X, y)

    def test_constant_column_skipped(self) -> None:
        rng = np.random.default_rng(7)
        X = pd.DataFrame({
            "constant": np.ones(50),
            "real": rng.normal(0, 1, 50),
            "real2": rng.normal(0, 1, 50),
        })
        y = pd.Series(rng.choice([-1, 0, 1], 50))
        sel = FeatureSelector()
        selected, report = sel.fit_transform(X, y)
        assert "constant" not in selected
        assert "constant" in report.removed_features
        assert report.removal_reasons["constant"] == "non_numeric_or_constant"

    def test_invalid_corr_threshold(self) -> None:
        with pytest.raises(ValueError):
            FeatureSelector(corr_threshold=0.0)
        with pytest.raises(ValueError):
            FeatureSelector(corr_threshold=1.0)
        with pytest.raises(ValueError):
            FeatureSelector(corr_threshold=1.5)


# ── 独立工具方法 ───────────────────────────────────────────────────────────────


class TestStandaloneUtils:
    def test_correlation_matrix(self) -> None:
        X, _ = make_correlated()
        sel = FeatureSelector()
        corr = sel.correlation_matrix(X)
        assert corr.shape == (3, 3)
        assert abs(corr.at["x1", "x1"] - 1.0) < 1e-9
        assert abs(corr.at["x1", "x2"]) > 0.9

    def test_compute_mi_scores(self) -> None:
        X, y = make_independent()
        sel = FeatureSelector()
        mi = sel.compute_mi_scores(X, y)
        assert set(mi.keys()) == {"a", "b", "c"}
        assert max(mi.values()) <= 1.0 + 1e-9
        assert min(mi.values()) >= 0.0 - 1e-9


# ── 回归测试：regression target ────────────────────────────────────────────────


class TestRegressionTarget:
    def test_regression_target_type(self) -> None:
        rng = np.random.default_rng(99)
        n = 50
        x1 = rng.normal(0, 1, n)
        x2 = 0.96 * x1 + 0.05 * rng.normal(0, 1, n)
        x3 = rng.normal(0, 1, n)
        X = pd.DataFrame({"x1": x1, "x2": x2, "x3": x3})
        y = pd.Series(x1 + rng.normal(0, 0.1, n))  # 连续目标
        sel = FeatureSelector(corr_threshold=0.85)
        selected, report = sel.fit_transform(X, y, target_type="regression")
        assert len(selected) >= 1
        assert report.n_original == 3
