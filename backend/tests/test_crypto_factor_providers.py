"""加密因子 provider 与注册表测试."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd

from quantpilot.factors.providers.core_crypto import CoreCryptoFactorProvider
from quantpilot.factors.providers.registry import FactorProviderRegistry


def _frame(rows: int = 80) -> pd.DataFrame:
    index = [datetime(2025, 1, 1, tzinfo=UTC) + timedelta(minutes=15 * i) for i in range(rows)]
    close = pd.Series([100_000 + i * 15 for i in range(rows)], index=index)
    frame = pd.DataFrame(
        {
            "open_15m": close * 0.99,
            "high_15m": close * 1.01,
            "low_15m": close * 0.98,
            "close_15m": close,
            "volume_15m": [1_000 + i for i in range(rows)],
            "close_1h": close * 0.995,
            "close_4h": close * 0.99,
            "close_1d": close * 0.98,
            "close_1w": close * 0.96,
        },
        index=index,
    )
    return frame


def test_core_crypto_factor_provider_emits_expected_columns() -> None:
    provider = CoreCryptoFactorProvider()
    features = provider.compute(_frame())

    expected = {
        "ema_10",
        "ema_20",
        "ema_50",
        "macd_hist",
        "atr_14",
        "adx_14",
        "plus_di_14",
        "minus_di_14",
        "rsi_14",
        "bb_width_20",
    }
    assert expected <= set(features.columns)


def test_factor_provider_registry_merges_provider_outputs() -> None:
    registry = FactorProviderRegistry(providers=[CoreCryptoFactorProvider()])
    features = registry.compute(_frame())

    assert "ema_20" in features.columns
    assert "macd_hist" in features.columns
    assert not features.empty
