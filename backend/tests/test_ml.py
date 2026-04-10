"""ML 策略模块测试 — T-4.2 验收."""
from __future__ import annotations

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pytest

from quantpilot.data.models import OHLCVBar
from quantpilot.ml.features import FeatureEngineer
from quantpilot.ml.registry import MLModelRegistry
from quantpilot.ml.strategy import LGBMStrategy


def _make_bars(n: int = 60) -> list[OHLCVBar]:
    base = datetime(2024, 1, 1, tzinfo=UTC)
    bars = []
    price = 100.0
    for i in range(n):
        price *= 1 + np.random.default_rng(i).uniform(-0.02, 0.02)
        bars.append(
            OHLCVBar(
                symbol="TEST",
                timeframe="1d",
                timestamp=base + timedelta(days=i),
                open=price * 0.99,
                high=price * 1.01,
                low=price * 0.98,
                close=round(price, 4),
                volume=float(1_000_000 + i * 1000),
            )
        )
    return bars


class TestFeatureEngineer:
    def test_compute_features_returns_dataframe(self) -> None:
        bars = _make_bars(60)
        fe = FeatureEngineer()
        df = fe.compute(bars)
        assert len(df) > 0
        assert "returns" in df.columns

    def test_feature_columns_present(self) -> None:
        bars = _make_bars(60)
        fe = FeatureEngineer()
        df = fe.compute(bars)
        expected_cols = {"returns", "volatility", "momentum", "close"}
        assert expected_cols.issubset(set(df.columns))

    def test_no_all_nan_columns(self) -> None:
        bars = _make_bars(60)
        fe = FeatureEngineer()
        df = fe.compute(bars)
        assert not df.isnull().all().any()

    def test_minimum_bars_required(self) -> None:
        bars = _make_bars(5)
        fe = FeatureEngineer()
        df = fe.compute(bars)
        assert len(df) >= 0  # may be empty — no crash


class TestLGBMStrategy:
    def test_fit_and_predict(self) -> None:
        bars = _make_bars(80)
        fe = FeatureEngineer()
        df = fe.compute(bars)
        strat = LGBMStrategy()
        strat.fit(df)
        preds = strat.predict(df.tail(10))
        assert len(preds) == 10
        assert all(p in {-1, 0, 1} for p in preds)

    def test_predict_before_fit_raises(self) -> None:
        bars = _make_bars(40)
        fe = FeatureEngineer()
        df = fe.compute(bars)
        strat = LGBMStrategy()
        with pytest.raises(RuntimeError, match="未训练"):
            strat.predict(df)


class TestMLModelRegistry:
    def test_save_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bars = _make_bars(80)
            fe = FeatureEngineer()
            df = fe.compute(bars)
            strat = LGBMStrategy()
            strat.fit(df)

            registry = MLModelRegistry(base_dir=Path(tmpdir))
            registry.save("test_model", strat)

            models = registry.list_models()
            assert "test_model" in models

            loaded = registry.load("test_model")
            assert loaded is not None
            preds = loaded.predict(df.tail(5))
            assert len(preds) == 5

    def test_load_nonexistent_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = MLModelRegistry(base_dir=Path(tmpdir))
            result = registry.load("ghost_model")
            assert result is None
