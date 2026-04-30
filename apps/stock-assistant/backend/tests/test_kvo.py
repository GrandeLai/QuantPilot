"""Tests for Klinger Volume Oscillator (KVO) — Phase F.68.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.kvo.engine import (
    _classify_signal,
    _compute_kvo_score,
    _compute_kvo_series,
    compute_kvo,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv_df(
    n: int,
    start: float = 100.0,
    step: float = 0.5,
    volume: int = 1_000_000,
) -> pd.DataFrame:
    idx    = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [start + i * step for i in range(n)]
    return pd.DataFrame(
        {
            "Open":   closes,
            "High":   [c + 1.0 for c in closes],
            "Low":    [c - 1.0 for c in closes],
            "Close":  closes,
            "Volume": [volume] * n,
        },
        index=idx,
    )


def _make_declining_df(n: int, start: float = 200.0, step: float = 0.3) -> pd.DataFrame:
    idx    = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [start - i * step for i in range(n)]
    return pd.DataFrame(
        {
            "Open":   closes,
            "High":   [c + 1.0 for c in closes],
            "Low":    [c - 1.0 for c in closes],
            "Close":  closes,
            "Volume": [1_000_000] * n,
        },
        index=idx,
    )


def _mock_ticker(df: pd.DataFrame) -> MagicMock:
    tk = MagicMock()
    tk.history.return_value = df
    return tk


# ---------------------------------------------------------------------------
# TestComputeKVOSeries
# ---------------------------------------------------------------------------

class TestComputeKVOSeries:
    def test_returns_two_series(self):
        df = _make_ohlcv_df(200)
        result = _compute_kvo_series(df["High"], df["Low"], df["Close"], df["Volume"])
        assert len(result) == 2

    def test_lengths_match_input(self):
        df = _make_ohlcv_df(200)
        kvo, sig = _compute_kvo_series(df["High"], df["Low"], df["Close"], df["Volume"])
        assert len(kvo) == len(sig) == 200

    def test_bullish_surge_positive_kvo(self):
        """Price flat then surges → EMA(34) reacts faster → KVO > 0."""
        idx    = pd.date_range("2022-01-01", periods=160, freq="B")
        closes = [100.0] * 80 + [100.0 + i * 2.0 for i in range(80)]
        df = pd.DataFrame({
            "High":   [c + 1.0 for c in closes],
            "Low":    [c - 1.0 for c in closes],
            "Close":  closes,
            "Volume": [1_000_000] * 160,
        }, index=idx)
        kvo, _ = _compute_kvo_series(df["High"], df["Low"], df["Close"], df["Volume"])
        assert float(kvo.iloc[-1]) > 0.0

    def test_bearish_surge_negative_kvo(self):
        """Price flat then crashes → EMA(34) reacts faster → KVO < 0."""
        idx    = pd.date_range("2022-01-01", periods=160, freq="B")
        closes = [200.0] * 80 + [200.0 - i * 2.0 for i in range(80)]
        df = pd.DataFrame({
            "High":   [c + 1.0 for c in closes],
            "Low":    [c - 1.0 for c in closes],
            "Close":  closes,
            "Volume": [1_000_000] * 160,
        }, index=idx)
        kvo, _ = _compute_kvo_series(df["High"], df["Low"], df["Close"], df["Volume"])
        assert float(kvo.iloc[-1]) < 0.0

    def test_no_inf_values(self):
        import math
        df = _make_ohlcv_df(200)
        kvo, sig = _compute_kvo_series(df["High"], df["Low"], df["Close"], df["Volume"])
        for s in (kvo, sig):
            assert all(math.isfinite(v) for v in s.values)

    def test_zero_volume_no_crash(self):
        """Zero volume should not raise."""
        df = _make_ohlcv_df(200, volume=0)
        kvo, sig = _compute_kvo_series(df["High"], df["Low"], df["Close"], df["Volume"])
        assert len(kvo) == 200


# ---------------------------------------------------------------------------
# TestComputeKVOScore
# ---------------------------------------------------------------------------

class TestComputeKVOScore:
    def _make_series(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_all_bullish_high_score(self):
        series = self._make_series([float(i) for i in range(-50, 51)])
        score = _compute_kvo_score(40.0, 20.0, series)
        assert score >= 60.0

    def test_all_bearish_low_score(self):
        series = self._make_series([float(i) for i in range(-50, 0)])
        score = _compute_kvo_score(-20.0, 10.0, series)
        assert score < 40.0

    def test_score_in_range(self):
        series = self._make_series([float(i) for i in range(-50, 51)])
        for kvo, sig in [(30.0, 10.0), (-30.0, -10.0)]:
            score = _compute_kvo_score(kvo, sig, series)
            assert 0.0 <= score <= 100.0

    def test_short_series_fallback(self):
        series = self._make_series([1.0, 2.0, 3.0])
        score = _compute_kvo_score(10.0, 5.0, series)
        assert 0.0 <= score <= 100.0


# ---------------------------------------------------------------------------
# TestClassifySignal
# ---------------------------------------------------------------------------

class TestClassifySignal:
    def test_strong_bull(self):
        assert _classify_signal(85.0) == "strong_bull"

    def test_bull(self):
        assert _classify_signal(65.0) == "bull"

    def test_neutral(self):
        assert _classify_signal(50.0) == "neutral"

    def test_bear(self):
        assert _classify_signal(30.0) == "bear"

    def test_strong_bear(self):
        assert _classify_signal(10.0) == "strong_bear"

    def test_none_returns_no_data(self):
        assert _classify_signal(None) == "no_data"

    def test_boundary_80(self):
        assert _classify_signal(80.0) == "strong_bull"

    def test_boundary_60(self):
        assert _classify_signal(60.0) == "bull"

    def test_boundary_40(self):
        assert _classify_signal(40.0) == "neutral"

    def test_boundary_20(self):
        assert _classify_signal(20.0) == "bear"


# ---------------------------------------------------------------------------
# TestComputeKVOIntegration
# ---------------------------------------------------------------------------

class TestComputeKVOIntegration:
    @patch("quantpilot_stock.kvo.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_kvo("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.kvo.engine.yf.Ticker")
    def test_fields_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_kvo("AAPL")
        assert isinstance(result.kvo_above_signal, bool)
        assert isinstance(result.kvo_positive, bool)
        assert result.kvo_value is not None
        assert result.signal_value is not None

    @patch("quantpilot_stock.kvo.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_kvo("AAPL")
        assert 0.0 <= result.kvo_score <= 100.0

    @patch("quantpilot_stock.kvo.engine.yf.Ticker")
    def test_rising_stock_positive_kvo(self, mock_yf):
        """Flat price then sharp surge → KVO should be positive (fast EMA > slow EMA)."""
        idx    = pd.date_range("2022-01-01", periods=300, freq="B")
        closes = [100.0] * 150 + [100.0 + i * 2.0 for i in range(150)]
        df = pd.DataFrame({
            "Open":   closes,
            "High":   [c + 1.0 for c in closes],
            "Low":    [c - 1.0 for c in closes],
            "Close":  closes,
            "Volume": [2_000_000] * 300,
        }, index=idx)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_kvo("AAPL")
        assert result.kvo_positive is True

    @patch("quantpilot_stock.kvo.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_kvo("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.kvo.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_kvo("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.kvo.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_kvo("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.kvo.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_kvo("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}


# ---------------------------------------------------------------------------
# TestKVOAPI
# ---------------------------------------------------------------------------

class TestKVOAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/kvo")
        assert resp.status_code == 422

    @patch("quantpilot_stock.kvo.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/kvo?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.kvo.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/kvo?ticker=AAPL").json()
        for f in ["ticker", "kvo_value", "signal_value", "kvo_above_signal",
                  "kvo_positive", "kvo_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.kvo.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/kvo?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
