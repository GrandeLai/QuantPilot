"""动态特征筛选器 — 皮尔逊去冗余 + 互信息排序.

Pipeline 位置（两条调用路径）：

  路径 A（研究 walk-forward）
    CryptoFeaturePipeline.compute()
        ↓  pd.DataFrame（含全量因子列 + 标签列）
    CryptoResearchService._feature_columns()
        ↓  list[str]（全量特征名）
    *** FeatureSelector.fit_transform() ***
        ↓  list[str]（筛选后特征名）+ SelectionReport
    CryptoResearchService._fit_multiclass()
        ↓  LGBMClassifier

  路径 B（简单训练接口）
    FeatureEngineer.compute()
        ↓  pd.DataFrame（含特征列 + "target" 列）
    *** FeatureSelector.fit_transform() ***
        ↓  list[str]（筛选后特征名）+ SelectionReport
    LGBMStrategy.fit(df, feature_columns=selected)
        ↓  已训练的模型
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd
from loguru import logger


# ── 筛选结果数据结构 ──────────────────────────────────────────────────────────


@dataclass
class SelectionReport:
    """特征筛选结果报告，记录整个筛选过程的决策细节.

    Attributes
    ----------
    selected_features:
        保留的特征列名列表（顺序与输入 X.columns 一致）。
    removed_features:
        被剔除的特征列名列表（含冗余特征 + 非数值 / 常数列）。
    removal_reasons:
        每个被剔除特征的原因，格式示例：

        - ``"corr=0.923>0.85_with:vwap_dev_20"``  — 与更优特征高度相关；
        - ``"non_numeric_or_constant"``             — 数据类型不合法或方差为零。
    mi_scores:
        各特征与目标变量的互信息得分，已归一化到 [0, 1]
        （最高 MI 特征的得分为 1.0）。
    corr_matrix:
        完整的皮尔逊相关矩阵（仅覆盖参与筛选的数值型非常数特征）。
    corr_threshold:
        本次筛选使用的相关性阈值。
    n_original:
        筛选前的特征总数（即输入 X.columns 的列数）。
    n_selected:
        筛选后保留的特征数。
    """

    selected_features: list[str]
    removed_features: list[str]
    removal_reasons: dict[str, str]
    mi_scores: dict[str, float]
    corr_matrix: pd.DataFrame
    corr_threshold: float
    n_original: int
    n_selected: int


# ── 主类 ──────────────────────────────────────────────────────────────────────


class FeatureSelector:
    """动态特征筛选器：皮尔逊相关去冗余 + 互信息排序.

    算法三步：

    1. **皮尔逊相关矩阵**：计算所有特征对的绝对相关系数，
       识别超过 ``corr_threshold`` 的高相关对；

    2. **互信息评分**：用 ``sklearn.feature_selection.mutual_info_classif``
       （或 ``mutual_info_regression``）计算每个特征与目标变量的信息相关度；

    3. **贪心去冗余**：按 MI 得分降序遍历特征，
       对每个尚未被移除的特征，将所有与其高度相关（|corr| > threshold）
       且 MI 更低的特征标记为冗余并移除。

    这样保证：在每一对相关特征中，总是保留信息量更高的那个。

    典型用法::

        selector = FeatureSelector(corr_threshold=0.85)
        selected_cols, report = selector.fit_transform(
            X=features[feature_columns],
            y=features["target_class"],
            target_type="classification",
        )
        model.fit(features[selected_cols], features["target_class"])

    参见模块 docstring 了解在两条 pipeline 路径中的确切调用位置。
    """

    def __init__(self, corr_threshold: float = 0.85, random_state: int = 42) -> None:
        """
        Parameters
        ----------
        corr_threshold:
            皮尔逊相关系数绝对值阈值，超过此值的特征对视为冗余。
            取值范围 (0, 1)，默认 0.85。
            - 较高阈值（0.9+）：只移除极端冗余，保留较多特征；
            - 较低阈值（0.7~0.8）：更激进去冗余，适合高维特征空间。
        random_state:
            sklearn 互信息计算的随机种子，用于保证结果可复现。
        """
        if not 0.0 < corr_threshold < 1.0:
            raise ValueError(f"corr_threshold 必须在 (0, 1) 之间，实际: {corr_threshold}")
        self.corr_threshold = corr_threshold
        self.random_state = random_state

    # ── 主接口 ────────────────────────────────────────────────────────────────

    def fit_transform(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        *,
        target_type: Literal["classification", "regression"] = "classification",
    ) -> tuple[list[str], SelectionReport]:
        """计算相关矩阵和互信息，返回筛选后的特征列名列表及详细报告.

        Parameters
        ----------
        X:
            特征 DataFrame（不含目标列）。行索引为时间戳或任意索引。
            支持含 NaN 的输入——将自动对 ``X`` 和 ``y`` 做行对齐后 dropna。
        y:
            目标 Series，与 X 行索引对齐。
            - 分类任务：整数或类别标签（如 -1 / 0 / 1）；
            - 回归任务：连续浮点数。
        target_type:
            指定目标类型以选择对应的 MI 计算方式：
            - ``"classification"``：调用 ``mutual_info_classif``（离散标签）；
            - ``"regression"``：调用 ``mutual_info_regression``（连续目标）。

        Returns
        -------
        selected_features : list[str]
            筛选后保留的特征列名，顺序与 X.columns 保持一致。
        report : SelectionReport
            详细筛选报告，含相关矩阵、MI 得分、移除原因等。

        Raises
        ------
        ValueError
            X 为空，或 dropna 后有效样本数不足 10 行。
        """
        if X.empty:
            raise ValueError("输入 DataFrame X 不能为空")

        # 行对齐 + 去 NaN（corr/MI 计算均要求完整数据）
        aligned = pd.concat([X, y.rename("__target__")], axis=1).dropna()
        if len(aligned) < 10:
            raise ValueError(
                f"dropna 后有效样本数不足 10 行（实际 {len(aligned)} 行），"
                "请检查数据质量或增加输入数据量"
            )

        X_clean = aligned.drop(columns="__target__")
        y_clean = aligned["__target__"]

        # 筛除非数值型和常数列（std ≈ 0 的列对 corr/MI 无意义）
        numeric_valid_cols = [
            c for c in X_clean.columns
            if pd.api.types.is_numeric_dtype(X_clean[c]) and X_clean[c].std() > 1e-8
        ]
        skipped = [c for c in X.columns if c not in set(numeric_valid_cols)]

        if len(numeric_valid_cols) == 0:
            raise ValueError("所有输入列均为常数或非数值型，无法执行特征筛选")

        X_valid = X_clean[numeric_valid_cols]
        all_features = list(numeric_valid_cols)  # 保持原始列顺序

        # ── Step 1：皮尔逊相关矩阵 ─────────────────────────────────────────
        corr_matrix = X_valid.corr(method="pearson")

        # ── Step 2：互信息得分 ──────────────────────────────────────────────
        mi = self._compute_mi(X_valid, y_clean, target_type=target_type)

        # ── Step 3：贪心去冗余 ──────────────────────────────────────────────
        selected, removed, removal_reasons = self._greedy_deduplicate(
            all_features=all_features,
            corr_matrix=corr_matrix,
            mi_scores=mi,
        )

        # 合并跳过列（非数值/常数）的移除记录
        all_removed = removed + skipped
        for c in skipped:
            removal_reasons[c] = "non_numeric_or_constant"

        report = SelectionReport(
            selected_features=selected,
            removed_features=all_removed,
            removal_reasons=removal_reasons,
            mi_scores=mi,
            corr_matrix=corr_matrix,
            corr_threshold=self.corr_threshold,
            n_original=len(X.columns),
            n_selected=len(selected),
        )

        logger.info(
            "[FeatureSelector] {orig}→{sel} 特征"
            "（corr_threshold={thr}，移除 {nrm} 个高相关冗余：{examples}）",
            orig=report.n_original,
            sel=report.n_selected,
            thr=self.corr_threshold,
            nrm=len(removed),
            examples=removed[:5] if removed else "无",
        )

        return selected, report

    def correlation_matrix(self, X: pd.DataFrame) -> pd.DataFrame:
        """单独计算皮尔逊相关矩阵，不执行特征筛选.

        可用于可视化分析或调试，调用前无需提供目标变量。

        Parameters
        ----------
        X:
            特征 DataFrame（数值列）。

        Returns
        -------
        pd.DataFrame
            皮尔逊相关矩阵，行列均为特征名。
        """
        return X.select_dtypes(include="number").corr(method="pearson")

    def compute_mi_scores(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        *,
        target_type: Literal["classification", "regression"] = "classification",
    ) -> dict[str, float]:
        """单独计算各特征与目标的互信息得分，不执行特征筛选.

        Parameters
        ----------
        X:
            特征 DataFrame（数值列）。
        y:
            目标 Series。
        target_type:
            目标类型。

        Returns
        -------
        dict[str, float]
            特征名 → 归一化互信息得分（最大值为 1.0）。
        """
        aligned = pd.concat([X, y.rename("__target__")], axis=1).dropna()
        X_clean = aligned.drop(columns="__target__").select_dtypes(include="number")
        y_clean = aligned["__target__"]
        return self._compute_mi(X_clean, y_clean, target_type=target_type)

    # ── 私有方法 ──────────────────────────────────────────────────────────────

    def _compute_mi(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        *,
        target_type: Literal["classification", "regression"],
    ) -> dict[str, float]:
        """计算各特征与目标的互信息，归一化到 [0, 1]."""
        from sklearn.feature_selection import mutual_info_classif, mutual_info_regression

        compute_fn = (
            mutual_info_classif if target_type == "classification" else mutual_info_regression
        )
        raw_mi: np.ndarray = compute_fn(X.values, y.values, random_state=self.random_state)

        # 归一化（最高 MI 特征得分 = 1.0，避免除零）
        max_mi = float(raw_mi.max()) if raw_mi.max() > 0 else 1.0
        normalized = raw_mi / max_mi

        return {col: float(score) for col, score in zip(X.columns, normalized, strict=True)}

    def _greedy_deduplicate(
        self,
        *,
        all_features: list[str],
        corr_matrix: pd.DataFrame,
        mi_scores: dict[str, float],
    ) -> tuple[list[str], list[str], dict[str, str]]:
        """贪心去冗余：按 MI 降序保留信息量最大的特征.

        算法：
            1. 按 MI 降序排列所有特征；
            2. 依次遍历，对每个未被标记移除的特征 f：
               将所有尚未移除且与 f 绝对相关超过阈值的特征 g 标记为冗余移除；
            3. 返回按原始列顺序整理的 selected / removed 列表。

        时间复杂度：O(n²)，n 为特征数。典型特征数 < 100 时性能无忧。

        Returns
        -------
        (selected, removed, removal_reasons)
        """
        to_remove: set[str] = set()
        removal_reasons: dict[str, str] = {}

        # MI 降序 → 优先保留信息量更高的特征
        sorted_by_mi = sorted(
            all_features, key=lambda f: mi_scores.get(f, 0.0), reverse=True
        )

        for f in sorted_by_mi:
            if f in to_remove:
                continue  # f 已被标记移除，跳过

            # 检查 f 与其余特征的相关性，移除低 MI 的冗余特征
            for g in all_features:
                if g == f or g in to_remove:
                    continue
                if f not in corr_matrix.index or g not in corr_matrix.columns:
                    continue
                corr_val = corr_matrix.at[f, g]
                if not np.isnan(corr_val) and abs(corr_val) > self.corr_threshold:
                    to_remove.add(g)
                    removal_reasons[g] = (
                        f"corr={corr_val:.3f}>{self.corr_threshold}_with:{f}"
                        f"(mi:{mi_scores.get(f,0):.3f}>mi:{mi_scores.get(g,0):.3f})"
                    )

        # 保持原始列顺序
        selected = [f for f in all_features if f not in to_remove]
        removed = [f for f in all_features if f in to_remove]
        return selected, removed, removal_reasons
