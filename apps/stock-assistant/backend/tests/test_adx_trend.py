"""Tests for ADX Trend Strength Indicator — Phase F.35.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from quantpilot_stock.adx_trend.engine import (
    _classify_signal,
    _compute_adx,
    _wilder_smooth,
    compute_adx_trend,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlc_df(n: int, trend: float = 0.5, noise: float = 0.2) -> pd.DataFrame:
    """Build synthetic OHLC data with optional upward trend."""
    rng = np.random.default_rng(42)
    close = [100.0]
    for _ in range(n - 1):
        close.append(close[-1] + trend + rng.normal(0, noise))
    close_arr = np.array(close)
    high_arr = close_arr + abs(rng.normal(0.5, 0.2, n))
    low_arr = close_arr - abs(rng.normal(0.5, 0.2, n))
    idx = pd.date_range("2023-01-01", periods=n, freq="B")
    return pd.DataFrame({"High": high_arr, "Low": low_arr, "Close": close_arr}, index=idx)


def _mock_ticker(df: pd.DataFrame) -> MagicMock:
    tk = MagicMock()
    tk.history.return_value = df
    return tk


# ---------------------------------------------------------------------------
# TestWilderSmooth
# ---------------------------------------------------------------------------

class TestWilderSmooth:
    def test_constant_series_returns_constant(self):
        s = pd.Series([5.0] * 30)
        smoothed = _wilder_smooth(s, 14)
        # After burn-in, should stabilize around 5.0
        assert abs(smoothed.iloc[-1] - 5.0) < 0.01

    def test_output_length_matches_input(self):
        s = pd.Series([float(i) for i in range(50)])
        smoothed = _wilder_smooth(s, 14)
        assert len(smoothed) == len(s)


# ---------------------------------------------------------------------------
# TestComputeADX
# ---------------------------------------------------------------------------

class TestComputeADX:
    def test_returns_floats_for_adequate_data(self):
        df = _make_ohlc_df(100)
        adx, plus_di, minus_di, atr = _compute_adx(df["High"], df["Low"], df["Close"])
        assert adx is not None
        assert plus_di is not None
        assert minus_di is not None
        assert atr is not None

    def test_adx_in_range(self):
        df = _make_ohlc_df(100)
        adx, _, _, _ = _compute_adx(df["High"], df["Low"], df["Close"])
        assert adx is not None
        assert 0.0 <= adx <= 100.0

    def test_di_positive(self):
        df = _make_ohlc_df(100)
        _, plus_di, minus_di, _ = _compute_adx(df["High"], df["Low"], df["Close"])
        assert plus_di is not None and plus_di >= 0
        assert minus_di is not None and minus_di >= 0

    def test_insufficient_data_returns_none(self):
        df = _make_ohlc_df(20)  # < 30 bars needed
        adx, plus_di, minus_di, atr = _compute_adx(df["High"], df["Low"], df["Close"])
        assert adx is None

    def test_strong_uptrend_plus_di_higher(self):
        """Consistent uptrend → +DI should dominate -DI."""
        # Very strong uptrend, low noise
        df = _make_ohlc_df(200, trend=2.0, noise=0.05)
        _, plus_di, minus_di, _ = _compute_adx(df["High"], df["Low"], df["Close"])
        assert plus_di is not None and minus_di is not None
        assert plus_di > minus_di


# ---------------------------------------------------------------------------
# TestClassifySignal
# ---------------------------------------------------------------------------

class TestClassifySignal:
    def test_strong_uptrend(self):
        assert _classify_signal(45.0, 30.0, 10.0) == "strong_uptrend"

    def test_uptrend(self):
        assert _classify_signal(25.0, 20.0, 10.0) == "uptrend"

    def test_ranging_low_adx(self):
        assert _classify_signal(15.0, 20.0, 10.0) == "ranging"

    def test_downtrend(self):
        assert _classify_signal(25.0, 10.0, 20.0) == "downtrend"

    def test_strong_downtrend(self):
        assert _classify_signal(45.0, 10.0, 30.0) == "strong_downtrend"

    def test_none_adx_returns_no_data(self):
        assert _classify_signal(None, None, None) == "no_data"

    def test_ranging_boundary_exactly_20(self):
        # adx=20 is NOT < 20, so not ranging
        assert _classify_signal(20.0, 20.0, 10.0) == "uptrend"

    def test_strong_uptrend_boundary_40(self):
        assert _classify_signal(40.0, 20.0, 10.0) == "strong_uptrend"


# ---------------------------------------------------------------------------
# TestComputeADXTrendIntegration
# ---------------------------------------------------------------------------

class TestComputeADXTrendIntegration:
    @patch("quantpilot_stock.adx_trend.engine.yf.Ticker")
    def test_data_available_true(self, mock_yf):
        df = _make_ohlc_df(150)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_adx_trend("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.adx_trend.engine.yf.Ticker")
    def test_adx_populated(self, mock_yf):
        df = _make_ohlc_df(150)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_adx_trend("AAPL")
        assert result.adx is not None

    @patch("quantpilot_stock.adx_trend.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlc_df(150)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_adx_trend("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.adx_trend.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlc_df(20)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_adx_trend("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.adx_trend.engine.yf.Ticker")
    def test_yfinance_exception_data_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_adx_trend("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.adx_trend.engine.yf.Ticker")
    def test_trend_strength_populated(self, mock_yf):
        df = _make_ohlc_df(150)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_adx_trend("AAPL")
        assert result.trend_strength in {"strong", "moderate", "weak", "none"}


# ---------------------------------------------------------------------------
# TestADXTrendAPI
# ---------------------------------------------------------------------------

class TestADXTrendAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/adx-trend")
        assert resp.status_code == 422

    @patch("quantpilot_stock.adx_trend.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlc_df(150)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/adx-trend?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.adx_trend.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlc_df(150)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/adx-trend?ticker=AAPL").json()
        for f in ["ticker", "adx", "plus_di", "minus_di", "signal", "trend_strength", "data_available", "interpretation"]:
            assert f in body

    @patch("quantpilot_stock.adx_trend.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/adx-trend?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
