"""Tests for Williams %R — Phase F.44.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.williams_r.engine import (
    _classify_signal,
    _compute_williams_r_series,
    _compute_wr_score,
    compute_williams_r,
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
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [start + i * step for i in range(n)]
    return pd.DataFrame({
        "Open": closes,
        "High": [c + 1.0 for c in closes],
        "Low": [c - 1.0 for c in closes],
        "Close": closes,
        "Volume": [volume] * n,
    }, index=idx)


def _make_declining_ohlcv(n: int, start: float = 150.0, step: float = 0.5) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [start - i * step for i in range(n)]
    return pd.DataFrame({
        "Open": closes,
        "High": [c + 1.0 for c in closes],
        "Low": [c - 1.0 for c in closes],
        "Close": closes,
        "Volume": [1_000_000] * n,
    }, index=idx)


def _mock_ticker(df: pd.DataFrame) -> MagicMock:
    tk = MagicMock()
    tk.history.return_value = df
    return tk


# ---------------------------------------------------------------------------
# TestComputeWilliamsRSeries
# ---------------------------------------------------------------------------

class TestComputeWilliamsRSeries:
    def test_close_at_high_wr_zero(self):
        """When close == highest high → %R = 0."""
        idx = pd.date_range("2022-01-01", periods=50, freq="B")
        # Fixed range: High=102, Low=100, Close=102 (at high)
        high = pd.Series([102.0] * 50, index=idx)
        low = pd.Series([100.0] * 50, index=idx)
        close = pd.Series([102.0] * 50, index=idx)
        wr = _compute_williams_r_series(high, low, close)
        assert abs(float(wr.iloc[-1]) - 0.0) < 0.01

    def test_close_at_low_wr_minus_100(self):
        """When close == lowest low → %R = -100."""
        idx = pd.date_range("2022-01-01", periods=50, freq="B")
        high = pd.Series([102.0] * 50, index=idx)
        low = pd.Series([100.0] * 50, index=idx)
        close = pd.Series([100.0] * 50, index=idx)
        wr = _compute_williams_r_series(high, low, close)
        assert abs(float(wr.iloc[-1]) - (-100.0)) < 0.01

    def test_close_at_midpoint_wr_minus_50(self):
        """When close at midpoint → %R = -50."""
        idx = pd.date_range("2022-01-01", periods=50, freq="B")
        high = pd.Series([102.0] * 50, index=idx)
        low = pd.Series([100.0] * 50, index=idx)
        close = pd.Series([101.0] * 50, index=idx)
        wr = _compute_williams_r_series(high, low, close)
        assert abs(float(wr.iloc[-1]) - (-50.0)) < 0.01

    def test_length_matches_input(self):
        df = _make_ohlcv_df(100)
        wr = _compute_williams_r_series(df["High"], df["Low"], df["Close"])
        assert len(wr) == len(df)

    def test_wr_in_range(self):
        df = _make_ohlcv_df(100)
        wr = _compute_williams_r_series(df["High"], df["Low"], df["Close"])
        valid = wr.dropna()
        assert float(valid.min()) >= -100.0
        assert float(valid.max()) <= 0.0

    def test_rising_stock_wr_near_zero(self):
        """Consistently rising → close near the high of recent range → %R near 0."""
        df = _make_ohlcv_df(100, step=1.0)
        wr = _compute_williams_r_series(df["High"], df["Low"], df["Close"])
        # For monotone rising: close is near the top of the 14-period range
        assert float(wr.iloc[-1]) > -50.0

    def test_declining_stock_wr_near_minus_100(self):
        """Consistently declining → close near the low of recent range."""
        df = _make_declining_ohlcv(100, step=1.0)
        wr = _compute_williams_r_series(df["High"], df["Low"], df["Close"])
        assert float(wr.iloc[-1]) < -50.0


# ---------------------------------------------------------------------------
# TestComputeWRScore
# ---------------------------------------------------------------------------

class TestComputeWRScore:
    def test_wr_zero_score_100(self):
        assert abs(_compute_wr_score(0.0) - 100.0) < 0.01

    def test_wr_minus_100_score_0(self):
        assert abs(_compute_wr_score(-100.0) - 0.0) < 0.01

    def test_wr_minus_50_score_50(self):
        assert abs(_compute_wr_score(-50.0) - 50.0) < 0.01

    def test_score_clipped(self):
        assert _compute_wr_score(10.0) <= 100.0
        assert _compute_wr_score(-110.0) >= 0.0


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
# TestComputeWilliamsRIntegration
# ---------------------------------------------------------------------------

class TestComputeWilliamsRIntegration:
    @patch("quantpilot_stock.williams_r.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_williams_r("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.williams_r.engine.yf.Ticker")
    def test_wr_populated_and_in_range(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_williams_r("AAPL")
        assert result.williams_r is not None
        assert -100.0 <= result.williams_r <= 0.0

    @patch("quantpilot_stock.williams_r.engine.yf.Ticker")
    def test_rising_stock_bull_score(self, mock_yf):
        df = _make_ohlcv_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_williams_r("AAPL")
        assert result.wr_score > 50.0

    @patch("quantpilot_stock.williams_r.engine.yf.Ticker")
    def test_declining_stock_bear_score(self, mock_yf):
        df = _make_declining_ohlcv(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_williams_r("AAPL")
        assert result.wr_score < 50.0

    @patch("quantpilot_stock.williams_r.engine.yf.Ticker")
    def test_overbought_flag(self, mock_yf):
        """Close at high → %R=0 > -20 → overbought."""
        idx = pd.date_range("2022-01-01", periods=200, freq="B")
        df = pd.DataFrame({
            "Open": [102.0] * 200,
            "High": [102.0] * 200,
            "Low": [100.0] * 200,
            "Close": [102.0] * 200,
            "Volume": [1_000_000] * 200,
        }, index=idx)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_williams_r("AAPL")
        assert result.overbought is True

    @patch("quantpilot_stock.williams_r.engine.yf.Ticker")
    def test_oversold_flag(self, mock_yf):
        """Close at low → %R=-100 < -80 → oversold."""
        idx = pd.date_range("2022-01-01", periods=200, freq="B")
        df = pd.DataFrame({
            "Open": [100.0] * 200,
            "High": [102.0] * 200,
            "Low": [100.0] * 200,
            "Close": [100.0] * 200,
            "Volume": [1_000_000] * 200,
        }, index=idx)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_williams_r("AAPL")
        assert result.oversold is True

    @patch("quantpilot_stock.williams_r.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_williams_r("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.williams_r.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_williams_r("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.williams_r.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_williams_r("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.williams_r.engine.yf.Ticker")
    def test_score_bounds(self, mock_yf):
        for df in [_make_ohlcv_df(200, step=3.0), _make_declining_ohlcv(200, step=3.0)]:
            mock_yf.return_value = _mock_ticker(df)
            result = compute_williams_r("AAPL")
            assert 0.0 <= result.wr_score <= 100.0

    @patch("quantpilot_stock.williams_r.engine.yf.Ticker")
    def test_direction_populated(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_williams_r("AAPL")
        assert result.wr_direction in ("rising", "falling", "flat")


# ---------------------------------------------------------------------------
# TestWilliamsRAPI
# ---------------------------------------------------------------------------

class TestWilliamsRAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/williams-r")
        assert resp.status_code == 422

    @patch("quantpilot_stock.williams_r.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/williams-r?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.williams_r.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/williams-r?ticker=AAPL").json()
        for f in ["ticker", "williams_r", "overbought", "oversold",
                  "wr_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.williams_r.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/williams-r?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
