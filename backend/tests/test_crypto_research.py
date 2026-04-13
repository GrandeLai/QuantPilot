"""OKX 多时间维度加密研究栈测试."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from quantpilot.data.models import OHLCVBar
from quantpilot.data.storage import MarketDataStorage
from quantpilot.ml.crypto_features import CryptoFeaturePipeline
from quantpilot.research.crypto_dataset import MultiTimeframeDatasetBuilder
from quantpilot.research.validation import TimeSeriesValidationConfig, build_walk_forward_windows


def _make_bar(
    *,
    symbol: str,
    timeframe: str,
    timestamp: datetime,
    close: float,
    volume: float = 1_000.0,
) -> OHLCVBar:
    return OHLCVBar(
        symbol=symbol,
        timeframe=timeframe,
        timestamp=timestamp,
        open=close * 0.99,
        high=close * 1.01,
        low=close * 0.98,
        close=close,
        volume=volume,
    )


def _seed_multitimeframe_bars(storage: MarketDataStorage, symbol: str = "BTC-USDT") -> None:
    base = datetime(2025, 1, 1, tzinfo=UTC)

    bars_15m: list[OHLCVBar] = []
    bars_1h: list[OHLCVBar] = []
    bars_4h: list[OHLCVBar] = []
    bars_1d: list[OHLCVBar] = []
    bars_1w: list[OHLCVBar] = []

    close = 100_000.0
    for i in range(96):
        ts = base + timedelta(minutes=15 * i)
        close += 25.0
        bars_15m.append(_make_bar(symbol=symbol, timeframe="15m", timestamp=ts, close=close, volume=1_000 + i))

    for i in range(24):
        ts = base + timedelta(hours=i)
        bars_1h.append(_make_bar(symbol=symbol, timeframe="1h", timestamp=ts, close=99_000 + i * 40, volume=4_000 + i))

    for i in range(12):
        ts = base + timedelta(hours=4 * i)
        bars_4h.append(_make_bar(symbol=symbol, timeframe="4h", timestamp=ts, close=98_000 + i * 80, volume=16_000 + i))

    for i in range(10):
        ts = base + timedelta(days=i)
        bars_1d.append(_make_bar(symbol=symbol, timeframe="1d", timestamp=ts, close=97_000 + i * 120, volume=64_000 + i))

    for i in range(4):
        ts = base + timedelta(days=7 * i)
        bars_1w.append(_make_bar(symbol=symbol, timeframe="1w", timestamp=ts, close=96_000 + i * 250, volume=256_000 + i))

    storage.upsert_bars(bars_15m + bars_1h + bars_4h + bars_1d + bars_1w)


@pytest.fixture
def storage() -> MarketDataStorage:
    """内存研究数据存储."""
    return MarketDataStorage(db_path=":memory:")


def test_multitimeframe_dataset_builder_aligns_higher_timeframes(storage: MarketDataStorage) -> None:
    _seed_multitimeframe_bars(storage)
    builder = MultiTimeframeDatasetBuilder(storage)

    dataset = builder.build(
        symbol="BTC-USDT",
        base_timeframe="15m",
        higher_timeframes=["1h", "4h", "1d", "1w"],
        limit=64,
    )

    assert dataset.symbol == "BTC-USDT"
    assert dataset.base_timeframe == "15m"
    assert dataset.rows > 0
    assert {"close_15m", "close_1h", "close_4h", "close_1d", "close_1w"} <= set(dataset.frame.columns)
    first_ts = dataset.frame.index[0]
    assert dataset.frame.loc[first_ts, "timestamp_1h"] <= first_ts


def test_crypto_feature_pipeline_emits_core_indicators_and_targets(storage: MarketDataStorage) -> None:
    _seed_multitimeframe_bars(storage)
    builder = MultiTimeframeDatasetBuilder(storage)
    dataset = builder.build(
        symbol="BTC-USDT",
        base_timeframe="15m",
        higher_timeframes=["1h", "4h", "1d", "1w"],
        limit=80,
    )

    pipeline = CryptoFeaturePipeline()
    features = pipeline.compute(dataset.frame)

    expected = {
        "ema_20",
        "macd_hist",
        "atr_14",
        "adx_14",
        "plus_di_14",
        "minus_di_14",
        "close_1h_ratio",
        "target_class",
        "target_reversal",
    }
    assert expected <= set(features.columns)
    assert not features.empty


def test_walk_forward_windows_are_ordered_and_embargoed() -> None:
    config = TimeSeriesValidationConfig(train_size=40, test_size=10, step_size=10, embargo_size=2)
    windows = build_walk_forward_windows(total_rows=90, config=config)

    assert len(windows) == 4
    assert windows[0].train_end < windows[0].test_start
    assert windows[0].test_start - windows[0].train_end == 3
    assert windows[-1].test_end < 90
