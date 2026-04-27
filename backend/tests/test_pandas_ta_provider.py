"""PandasTaCryptoFactorProvider 单元测试."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from quantpilot.factors.providers.pandas_ta_crypto import PandasTaCryptoFactorProvider


# ── 测试数据工厂 ───────────────────────────────────────────────────────────────


def make_frame(n: int = 100, seed: int = 42) -> pd.DataFrame:
    """生成符合格式的最小多周期对齐数据集（仅含 15m OHLCV）."""
    rng = np.random.default_rng(seed)
    base_price = 30_000.0
    returns = rng.normal(0.0, 0.002, n)
    close = pd.Series(base_price * (1 + returns).cumprod())
    high = close * (1 + rng.uniform(0.001, 0.01, n))
    low = close * (1 - rng.uniform(0.001, 0.01, n))
    open_ = close.shift(1).fillna(close.iloc[0])
    volume = pd.Series(rng.uniform(500, 2000, n))
    return pd.DataFrame(
        {
            "open_15m": open_,
            "high_15m": high,
            "low_15m": low,
            "close_15m": close,
            "volume_15m": volume,
        }
    )


EXPECTED_COLUMNS = ["cci_20", "willr_14", "mfi_14", "stoch_k", "stoch_d", "roc_10", "dpo_20"]


# ── 基本输出结构 ──────────────────────────────────────────────────────────────


class TestOutputStructure:
    def test_returns_dataframe(self) -> None:
        provider = PandasTaCryptoFactorProvider()
        result = provider.compute(make_frame())
        assert isinstance(result, pd.DataFrame)

    def test_all_expected_columns_present(self) -> None:
        provider = PandasTaCryptoFactorProvider()
        result = provider.compute(make_frame())
        for col in EXPECTED_COLUMNS:
            assert col in result.columns, f"缺少列: {col}"

    def test_no_extra_columns(self) -> None:
        provider = PandasTaCryptoFactorProvider()
        result = provider.compute(make_frame())
        assert set(result.columns) == set(EXPECTED_COLUMNS)

    def test_row_count_matches_input(self) -> None:
        frame = make_frame(80)
        provider = PandasTaCryptoFactorProvider()
        result = provider.compute(frame)
        assert len(result) == len(frame)

    def test_index_matches_input(self) -> None:
        frame = make_frame()
        provider = PandasTaCryptoFactorProvider()
        result = provider.compute(frame)
        pd.testing.assert_index_equal(result.index, frame.index)


# ── 空数据输入 ────────────────────────────────────────────────────────────────


class TestEmptyInput:
    def test_empty_frame_returns_empty(self) -> None:
        provider = PandasTaCryptoFactorProvider()
        result = provider.compute(pd.DataFrame())
        assert isinstance(result, pd.DataFrame)
        assert result.empty


# ── Provider 名称 ─────────────────────────────────────────────────────────────


class TestProviderName:
    def test_name(self) -> None:
        assert PandasTaCryptoFactorProvider().name == "pandas_ta_crypto"


# ── 数值范围验证 ──────────────────────────────────────────────────────────────


class TestValueRanges:
    def test_willr_range(self) -> None:
        """Williams %R 应在 [-100, 0] 范围内."""
        provider = PandasTaCryptoFactorProvider()
        result = provider.compute(make_frame(100))
        valid = result["willr_14"].dropna()
        assert (valid >= -100).all(), "Williams %R 不应低于 -100"
        assert (valid <= 0).all(), "Williams %R 不应超过 0"

    def test_mfi_range(self) -> None:
        """MFI 应在 [0, 100] 范围内."""
        provider = PandasTaCryptoFactorProvider()
        result = provider.compute(make_frame(100))
        valid = result["mfi_14"].dropna()
        assert (valid >= 0).all(), "MFI 不应低于 0"
        assert (valid <= 100).all(), "MFI 不应超过 100"

    def test_stoch_k_range(self) -> None:
        """Stochastic %K 应在 [0, 100] 范围内."""
        provider = PandasTaCryptoFactorProvider()
        result = provider.compute(make_frame(100))
        valid = result["stoch_k"].dropna()
        assert (valid >= 0).all()
        assert (valid <= 100).all()

    def test_stoch_d_range(self) -> None:
        """Stochastic %D 应在 [0, 100] 范围内."""
        provider = PandasTaCryptoFactorProvider()
        result = provider.compute(make_frame(100))
        valid = result["stoch_d"].dropna()
        assert (valid >= 0).all()
        assert (valid <= 100).all()


# ── 前视污染检测 ──────────────────────────────────────────────────────────────


class TestNoLookahead:
    def test_early_rows_have_nan(self) -> None:
        """计算窗口期内的早期行应为 NaN（不存在前视填充）."""
        provider = PandasTaCryptoFactorProvider()
        result = provider.compute(make_frame(50))
        # roc_10 前 10 行应为 NaN
        assert result["roc_10"].iloc[:10].isna().all(), "roc_10 前 10 行应为 NaN"

    def test_later_rows_have_values(self) -> None:
        """充足数据后的行应有有效值（非全 NaN）."""
        provider = PandasTaCryptoFactorProvider()
        result = provider.compute(make_frame(100))
        # 最后 50 行的所有指标都应有值
        tail = result.iloc[-50:]
        for col in EXPECTED_COLUMNS:
            assert tail[col].notna().any(), f"{col} 末尾行不应全为 NaN"


# ── 与 CoreCryptoFactorProvider 无重叠 ────────────────────────────────────────


class TestNoColumnOverlap:
    def test_no_duplicate_with_core_columns(self) -> None:
        """pandas-ta 因子列名不应与 CoreCryptoFactorProvider 输出重叠."""
        from quantpilot.factors.providers.core_crypto import CoreCryptoFactorProvider

        provider_ta = PandasTaCryptoFactorProvider()
        provider_core = CoreCryptoFactorProvider()
        frame = make_frame(100)

        ta_cols = set(provider_ta.compute(frame).columns)
        core_cols = set(provider_core.compute(frame).columns)

        overlap = ta_cols & core_cols
        assert not overlap, f"列名重叠: {overlap}"


# ── 注册表集成 ────────────────────────────────────────────────────────────────


class TestRegistryIntegration:
    def test_included_in_default_pipeline(self) -> None:
        """PandasTaCryptoFactorProvider 应出现在 CryptoFeaturePipeline 默认注册表中."""
        from quantpilot.ml.crypto_features import CryptoFeaturePipeline

        pipeline = CryptoFeaturePipeline()
        names = pipeline._provider_registry.provider_names()
        assert "pandas_ta_crypto" in names

    def test_all_three_providers_in_default(self) -> None:
        """默认注册表应包含 core、advanced、pandas_ta 三个 provider."""
        from quantpilot.ml.crypto_features import CryptoFeaturePipeline

        pipeline = CryptoFeaturePipeline()
        names = pipeline._provider_registry.provider_names()
        assert "core_crypto" in names
        assert "advanced_crypto" in names
        assert "pandas_ta_crypto" in names
