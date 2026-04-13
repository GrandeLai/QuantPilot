"""加密研究 API 测试."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from quantpilot.data.models import OHLCVBar
from quantpilot.data.storage import MarketDataStorage


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


def _seed(storage: MarketDataStorage, symbol: str = "BTC-USDT") -> None:
    base = datetime(2025, 1, 1, tzinfo=UTC)
    bars: list[OHLCVBar] = []
    for i in range(240):
        ts = base + timedelta(minutes=15 * i)
        bars.append(_make_bar(symbol=symbol, timeframe="15m", timestamp=ts, close=100_000 + i * 10, volume=1_000 + i))
    for i in range(60):
        ts = base + timedelta(hours=i)
        bars.append(_make_bar(symbol=symbol, timeframe="1h", timestamp=ts, close=99_500 + i * 25, volume=4_000 + i))
    for i in range(30):
        ts = base + timedelta(hours=4 * i)
        bars.append(_make_bar(symbol=symbol, timeframe="4h", timestamp=ts, close=99_000 + i * 50, volume=16_000 + i))
    for i in range(20):
        ts = base + timedelta(days=i)
        bars.append(_make_bar(symbol=symbol, timeframe="1d", timestamp=ts, close=98_000 + i * 100, volume=64_000 + i))
    for i in range(6):
        ts = base + timedelta(days=7 * i)
        bars.append(_make_bar(symbol=symbol, timeframe="1w", timestamp=ts, close=97_000 + i * 200, volume=256_000 + i))
    storage.upsert_bars(bars)


def test_crypto_research_dataset_summary(client: TestClient, monkeypatch) -> None:
    from quantpilot.api import data as data_api

    storage = MarketDataStorage(db_path=":memory:")
    _seed(storage)
    monkeypatch.setattr(data_api, "_storage", storage)

    response = client.post(
        "/api/crypto/research/dataset",
        json={
            "symbol": "BTC-USDT",
            "base_timeframe": "15m",
            "higher_timeframes": ["1h", "4h", "1d", "1w"],
            "limit": 120,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "BTC-USDT"
    assert body["base_timeframe"] == "15m"
    assert body["rows"] > 0
    assert "close_1h" in body["dataset_columns"]


def test_crypto_research_training_summary(client: TestClient, monkeypatch) -> None:
    from quantpilot.api import data as data_api

    storage = MarketDataStorage(db_path=":memory:")
    _seed(storage)
    monkeypatch.setattr(data_api, "_storage", storage)

    response = client.post(
        "/api/crypto/research/train",
        json={
            "symbol": "BTC-USDT",
            "base_timeframe": "15m",
            "higher_timeframes": ["1h", "4h", "1d", "1w"],
            "limit": 180,
            "validation": {
                "train_size": 60,
                "test_size": 20,
                "step_size": 20,
                "embargo_size": 2,
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "BTC-USDT"
    assert body["feature_count"] > 0
    assert body["validation_windows"] > 0
    assert set(body["latest_class_probabilities"].keys()) == {"-1", "0", "1"}
    assert "reversal_probability" in body
    assert body["market_regime"] in {"trend", "range", "high_volatility"}
    assert body["recommended_strategy_ids"]
    assert body["recommended_timeframes"]
    assert body["parameter_search_ready"] is True


def test_crypto_research_latest_returns_cached_summary(client: TestClient, monkeypatch) -> None:
    from quantpilot.api import data as data_api

    storage = MarketDataStorage(db_path=":memory:")
    _seed(storage)
    monkeypatch.setattr(data_api, "_storage", storage)

    train_response = client.post(
        "/api/crypto/research/train",
        json={
            "symbol": "BTC-USDT",
            "base_timeframe": "15m",
            "higher_timeframes": ["1h", "4h", "1d", "1w"],
            "limit": 180,
            "validation": {
                "train_size": 60,
                "test_size": 20,
                "step_size": 20,
                "embargo_size": 2,
            },
        },
    )
    assert train_response.status_code == 200

    latest_response = client.get("/api/crypto/research/latest?symbol=BTC-USDT&base_timeframe=15m")
    assert latest_response.status_code == 200
    latest = latest_response.json()
    assert latest["symbol"] == "BTC-USDT"
    assert latest["base_timeframe"] == "15m"
    assert latest["feature_count"] > 0
    assert latest["market_regime"] in {"trend", "range", "high_volatility"}


def test_crypto_research_optimize_returns_best_params(client: TestClient, monkeypatch) -> None:
    from quantpilot.api import data as data_api

    storage = MarketDataStorage(db_path=":memory:")
    _seed(storage)
    monkeypatch.setattr(data_api, "_storage", storage)

    response = client.post(
        "/api/crypto/research/optimize",
        json={
            "symbol": "BTC-USDT",
            "base_timeframe": "15m",
            "higher_timeframes": ["1h", "4h", "1d", "1w"],
            "limit": 180,
            "param_grid": {
                "fast_period": [5, 8],
                "slow_period": [20, 30],
                "vwap_window": [10, 20],
                "trailing_stop_pct": [0.02, 0.03],
                "max_hold_bars": [24, 48],
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["strategy_id"] == "vwap_ema_trend"
    assert body["best_params"]
    assert body["window_count"] > 0
    assert "mean_strategy_return" in body
