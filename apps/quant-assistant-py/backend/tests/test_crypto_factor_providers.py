"""加密因子 provider 与注册表测试."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from types import ModuleType

import pandas as pd

from quantpilot_quant.factors.providers.core_crypto import CoreCryptoFactorProvider
from quantpilot_quant.factors.providers.external_crypto import ExternalCryptoFactorProvider
from quantpilot_quant.factors.providers.registry import FactorProviderRegistry


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


def test_external_provider_gracefully_noops_when_dependency_missing() -> None:
    provider = ExternalCryptoFactorProvider(module_name="definitely_missing_crypto_factor_lib")
    features = provider.compute(_frame())

    assert features.empty
    assert list(features.index) == list(_frame().index)


def test_external_provider_can_adapt_third_party_module() -> None:
    module_name = "fake_crypto_factor_lib"
    fake_module = ModuleType(module_name)

    def build_features(frame: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "external_alpha": frame["close_15m"].pct_change().fillna(0.0),
                "external_beta": frame["volume_15m"].rolling(5, min_periods=1).mean(),
            },
            index=frame.index,
        )

    fake_module.build_features = build_features  # type: ignore[attr-defined]
    sys.modules[module_name] = fake_module
    try:
        provider = ExternalCryptoFactorProvider(module_name=module_name)
        features = provider.compute(_frame())
    finally:
        sys.modules.pop(module_name, None)

    assert {"external_alpha", "external_beta"} <= set(features.columns)


def test_factor_provider_registry_reports_available_provider_names() -> None:
    registry = FactorProviderRegistry(
        providers=[
            CoreCryptoFactorProvider(),
            ExternalCryptoFactorProvider(module_name="definitely_missing_crypto_factor_lib"),
        ]
    )

    assert registry.provider_names() == ["core_crypto", "external_crypto"]
    assert registry.available_provider_names() == ["core_crypto"]
