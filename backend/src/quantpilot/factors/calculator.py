"""因子研究计算器 — IC/IR 分析与分层回测."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class FactorICResult:
    """因子 IC/IR 分析结果."""

    ic: float             # 单期 IC（最新）
    ir: float             # IR = mean(IC) / std(IC)
    ic_mean: float
    ic_std: float
    n_periods: int


class FactorCalculator:
    """因子有效性分析：IC、IR、分层回测."""

    def compute_ic(
        self, factor: pd.Series, forward_return: pd.Series
    ) -> float:
        """计算单期 Spearman IC."""
        valid = pd.DataFrame({"f": factor, "r": forward_return}).dropna()
        if len(valid) < 5:
            return 0.0
        ic, _ = stats.spearmanr(valid["f"], valid["r"])
        return float(ic)

    def compute_ic_series(
        self, df: pd.DataFrame, window: int = 20
    ) -> list[float]:
        """滚动窗口计算 IC 序列.

        df 必须含 'factor' 和 'forward_return' 列。
        """
        ics: list[float] = []
        n = len(df)
        for start in range(0, n - window + 1, window):
            chunk = df.iloc[start : start + window]
            ic = self.compute_ic(chunk["factor"], chunk["forward_return"])
            ics.append(ic)
        return ics

    def compute_ir(self, ic_series: list[float]) -> FactorICResult:
        """从 IC 序列计算 IR."""
        if not ic_series:
            return FactorICResult(ic=0.0, ir=0.0, ic_mean=0.0, ic_std=0.0, n_periods=0)
        arr = np.array(ic_series)
        ic_mean = float(arr.mean())
        ic_std = float(arr.std()) if len(arr) > 1 else 0.0
        ir = ic_mean / ic_std if ic_std > 0 else 0.0
        return FactorICResult(
            ic=ic_series[-1],
            ir=ir,
            ic_mean=ic_mean,
            ic_std=ic_std,
            n_periods=len(ic_series),
        )

    def layered_returns(
        self,
        factor: pd.Series,
        forward_return: pd.Series,
        n_quantiles: int = 5,
    ) -> dict[str, float]:
        """分层回测：按因子分 N 组，返回各组平均收益率."""
        df = pd.DataFrame({"f": factor, "r": forward_return}).dropna()
        if len(df) < n_quantiles:
            return {f"Q{i+1}": 0.0 for i in range(n_quantiles)}
        df["quantile"] = pd.qcut(df["f"], q=n_quantiles, labels=False, duplicates="drop")
        result: dict[str, float] = {}
        for q in range(n_quantiles):
            group = df[df["quantile"] == q]["r"]
            result[f"Q{q+1}"] = float(group.mean()) if len(group) > 0 else 0.0
        return result
