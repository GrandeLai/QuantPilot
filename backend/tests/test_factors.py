"""因子研究测试 — T-3.2 验收."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quantpilot.factors.calculator import FactorCalculator, FactorICResult


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """构造含 factor、forward_return 列的测试数据."""
    np.random.seed(42)
    n = 100
    factor = np.random.randn(n)
    # Positively correlated forward returns (IC should be > 0)
    forward_return = factor * 0.5 + np.random.randn(n) * 0.3
    return pd.DataFrame({"factor": factor, "forward_return": forward_return})


class TestFactorICResult:
    def test_has_fields(self) -> None:
        r = FactorICResult(ic=0.35, ir=1.2, ic_mean=0.35, ic_std=0.29, n_periods=50)
        assert r.ic == 0.35
        assert r.ir == pytest.approx(1.2)


class TestFactorCalculator:
    def test_compute_ic(self, sample_df: pd.DataFrame) -> None:
        calc = FactorCalculator()
        ic = calc.compute_ic(sample_df["factor"], sample_df["forward_return"])
        assert isinstance(ic, float)
        assert -1.0 <= ic <= 1.0
        assert ic > 0.0  # positively correlated

    def test_compute_ic_series(self, sample_df: pd.DataFrame) -> None:
        calc = FactorCalculator()
        # Split into 10 windows of 10 bars each
        series = calc.compute_ic_series(sample_df, window=10)
        assert isinstance(series, list)
        assert len(series) > 0
        assert all(isinstance(v, float) for v in series)

    def test_compute_ir(self, sample_df: pd.DataFrame) -> None:
        calc = FactorCalculator()
        series = calc.compute_ic_series(sample_df, window=10)
        result = calc.compute_ir(series)
        assert isinstance(result, FactorICResult)
        assert result.n_periods == len(series)
        assert isinstance(result.ir, float)

    def test_layered_returns(self, sample_df: pd.DataFrame) -> None:
        calc = FactorCalculator()
        layers = calc.layered_returns(sample_df["factor"], sample_df["forward_return"], n_quantiles=5)
        assert len(layers) == 5
        assert all(isinstance(v, float) for v in layers.values())

    def test_empty_series_returns_zero_ic(self) -> None:
        calc = FactorCalculator()
        result = calc.compute_ir([])
        assert result.ic_mean == 0.0
        assert result.n_periods == 0
