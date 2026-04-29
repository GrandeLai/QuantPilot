"""Tests for Stochastic Oscillator — Phase F.40.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.stochastic.engine import (
    _classify_signal,
    _compute_stoch_score,
    _compute_stochastic_series,
    compute_stochastic,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlc_df(n: int, start: float = 100.0, step: float = 0.5) -> pd.DataFrame:
    """Rising OHLC prices."""
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [start + i * step for i in range(n)]
    highs = [c + 1.0 for c in closes]
    lows = [c - 1.0 for c in closes]
    return pd.DataFrame({"Open": closes, "High": highs, "Low": lows, "Close": closes}, index=idx)


def _make_declining_ohlc(n: int, start: float = 150.0, step: float = 0.5) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [start - i * step for i in range(n)]
    highs = [c + 1.0 for c in closes]
    lows = [c - 1.0 for c in closes]
    return pd.DataFrame({"Open": closes, "High": highs, "Low": lows, "Close": closes}, index=idx)


def _make_flat_ohlc(n: int, price: float = 100.0) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    return pd.DataFrame({
        "Open": [price] * n,
        "High": [price + 0.5] * n,
        "Low": [price - 0.5] * n,
        "Close": [price] * n,
    }, index=idx)


def _mock_ticker(df: pd.DataFrame) -> MagicMock:
    tk = MagicMock()
    tk.history.return_value = df
    return tk


# ---------------------------------------------------------------------------
# TestComputeStochasticSeries
# ---------------------------------------------------------------------------

class TestComputeStochasticSeries:
    def test_k_in_range(self):
        df = _make_ohlc_df(100)
        k, d = _compute_stochastic_series(df["High"], df["Low"], df["Close"])
        valid_k = k.dropna()
        assert all(0.0 <= v <= 100.0 for v in valid_k)

    def test_rising_stock_k_near_100(self):
        df = _make_ohlc_df(200, step=1.0)
        k, _ = _compute_stochastic_series(df["High"], df["Low"], df["Close"])
        # Consistently rising → close near highest high → %K near 100
        assert float(k.iloc[-1]) > 80.0

    def test_declining_stock_k_near_0(self):
        df = _make_declining_ohlc(200, step=1.0)
        k, _ = _compute_stochastic_series(df["High"], df["Low"], df["Close"])
        assert float(k.iloc[-1]) < 20.0

    def test_d_is_smoothed_k(self):
        df = _make_ohlc_df(100)
        k, d = _compute_stochastic_series(df["High"], df["Low"], df["Close"])
        # D is 3-period SMA of K, should be within K's range
        valid_d = d.dropna()
        assert all(0.0 <= v <= 100.0 for v in valid_d)

    def test_length_preserved(self):
        df = _make_ohlc_df(100)
        k, d = _compute_stochastic_series(df["High"], df["Low"], df["Close"])
        assert len(k) == len(df)
        assert len(d) == len(df)


# ---------------------------------------------------------------------------
# TestComputeStochScore
# ---------------------------------------------------------------------------

class TestComputeStochScore:
    def test_high_k_high_score(self):
        score = _compute_stoch_score(k=90.0, d=85.0, recent_bull_cross=False, recent_bear_cross=False)
        assert score >= 80.0

    def test_low_k_low_score(self):
        score = _compute_stoch_score(k=10.0, d=15.0, recent_bull_cross=False, recent_bear_cross=False)
        assert score <= 20.0

    def test_k_above_d_adds_score(self):
        s_below = _compute_stoch_score(k=50.0, d=55.0, recent_bull_cross=False, recent_bear_cross=False)
        s_above = _compute_stoch_score(k=50.0, d=45.0, recent_bull_cross=False, recent_bear_cross=False)
        assert s_above > s_below

    def test_bull_cross_adds_score(self):
        s_no = _compute_stoch_score(k=50.0, d=50.0, recent_bull_cross=False, recent_bear_cross=False)
        s_yes = _compute_stoch_score(k=50.0, d=50.0, recent_bull_cross=True, recent_bear_cross=False)
        assert s_yes > s_no

    def test_score_in_range(self):
        for k in [0.0, 20.0, 50.0, 80.0, 100.0]:
            score = _compute_stoch_score(k, d=50.0, recent_bull_cross=False, recent_bear_cross=False)
            assert 0.0 <= score <= 100.0

    def test_none_k_returns_50(self):
        score = _compute_stoch_score(None, None, False, False)
        assert score == 50.0


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
# TestComputeStochasticIntegration
# ---------------------------------------------------------------------------

class TestComputeStochasticIntegration:
    @patch("quantpilot_stock.stochastic.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlc_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stochastic("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.stochastic.engine.yf.Ticker")
    def test_k_d_populated(self, mock_yf):
        df = _make_ohlc_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stochastic("AAPL")
        assert result.k is not None
        assert result.d is not None
        assert 0.0 <= result.k <= 100.0

    @patch("quantpilot_stock.stochastic.engine.yf.Ticker")
    def test_rising_bull_score(self, mock_yf):
        df = _make_ohlc_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stochastic("AAPL")
        assert result.stoch_score > 50.0

    @patch("quantpilot_stock.stochastic.engine.yf.Ticker")
    def test_declining_bear_score(self, mock_yf):
        df = _make_declining_ohlc(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stochastic("AAPL")
        assert result.stoch_score < 50.0

    @patch("quantpilot_stock.stochastic.engine.yf.Ticker")
    def test_overbought_detected(self, mock_yf):
        df = _make_ohlc_df(200, step=2.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stochastic("AAPL")
        assert result.overbought is True

    @patch("quantpilot_stock.stochastic.engine.yf.Ticker")
    def test_oversold_detected(self, mock_yf):
        df = _make_declining_ohlc(200, step=2.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stochastic("AAPL")
        assert result.oversold is True

    @patch("quantpilot_stock.stochastic.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlc_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stochastic("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.stochastic.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlc_df(15)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stochastic("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.stochastic.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_stochastic("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.stochastic.engine.yf.Ticker")
    def test_score_bounds(self, mock_yf):
        for df in [_make_ohlc_df(200, step=3.0), _make_declining_ohlc(200, step=3.0)]:
            mock_yf.return_value = _mock_ticker(df)
            result = compute_stochastic("AAPL")
            assert 0.0 <= result.stoch_score <= 100.0


# ---------------------------------------------------------------------------
# TestStochasticAPI
# ---------------------------------------------------------------------------

class TestStochasticAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/stochastic")
        assert resp.status_code == 422

    @patch("quantpilot_stock.stochastic.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlc_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/stochastic?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.stochastic.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlc_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/stochastic?ticker=AAPL").json()
        for f in ["ticker", "k", "d", "overbought", "oversold",
                  "k_above_d", "stoch_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.stochastic.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/stochastic?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
