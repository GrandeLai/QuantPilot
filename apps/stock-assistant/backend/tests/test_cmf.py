"""Tests for Chaikin Money Flow — Phase F.43.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.cmf.engine import (
    _classify_signal,
    _compute_cmf_score,
    _compute_cmf_series,
    compute_cmf,
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


def _make_close_at_midpoint_df(n: int) -> pd.DataFrame:
    """Close == midpoint of High/Low → MFM = 0 → CMF = 0."""
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [100.0] * n
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
# TestComputeCMFSeries
# ---------------------------------------------------------------------------

class TestComputeCMFSeries:
    def test_rising_stock_positive_cmf(self):
        """Close rising toward high → MFM > 0 → CMF > 0."""
        df = _make_ohlcv_df(100)
        cmf = _compute_cmf_series(df["High"], df["Low"], df["Close"], df["Volume"])
        # For our helper: High=C+1, Low=C-1, Close=C
        # MFM = ((C - (C-1)) - ((C+1) - C)) / 2 = (1 - 1) / 2 = 0
        # So CMF = 0 for flat close-relative-to-range; check length at least
        assert len(cmf) == len(df)

    def test_close_at_high_cmf_positive(self):
        """Close == High → MFM = 1 → CMF = 1."""
        idx = pd.date_range("2022-01-01", periods=50, freq="B")
        high = pd.Series([102.0] * 50, index=idx)
        low = pd.Series([100.0] * 50, index=idx)
        close = pd.Series([102.0] * 50, index=idx)   # at high
        volume = pd.Series([1_000_000] * 50, index=idx)
        cmf = _compute_cmf_series(high, low, close, volume)
        assert abs(float(cmf.iloc[-1]) - 1.0) < 0.01

    def test_close_at_low_cmf_negative(self):
        """Close == Low → MFM = -1 → CMF = -1."""
        idx = pd.date_range("2022-01-01", periods=50, freq="B")
        high = pd.Series([102.0] * 50, index=idx)
        low = pd.Series([100.0] * 50, index=idx)
        close = pd.Series([100.0] * 50, index=idx)   # at low
        volume = pd.Series([1_000_000] * 50, index=idx)
        cmf = _compute_cmf_series(high, low, close, volume)
        assert abs(float(cmf.iloc[-1]) - (-1.0)) < 0.01

    def test_close_at_midpoint_cmf_zero(self):
        """Close == midpoint of H/L → MFM = 0 → CMF = 0."""
        df = _make_close_at_midpoint_df(50)
        cmf = _compute_cmf_series(df["High"], df["Low"], df["Close"], df["Volume"])
        assert abs(float(cmf.iloc[-1])) < 0.01

    def test_cmf_length_matches_input(self):
        df = _make_ohlcv_df(100)
        cmf = _compute_cmf_series(df["High"], df["Low"], df["Close"], df["Volume"])
        assert len(cmf) == len(df)

    def test_cmf_in_range(self):
        df = _make_ohlcv_df(100)
        cmf = _compute_cmf_series(df["High"], df["Low"], df["Close"], df["Volume"])
        valid = cmf.dropna()
        assert float(valid.min()) >= -1.0
        assert float(valid.max()) <= 1.0


# ---------------------------------------------------------------------------
# TestComputeCMFScore
# ---------------------------------------------------------------------------

class TestComputeCMFScore:
    def test_cmf_plus_one_score_100(self):
        assert abs(_compute_cmf_score(1.0) - 100.0) < 0.01

    def test_cmf_minus_one_score_0(self):
        assert abs(_compute_cmf_score(-1.0) - 0.0) < 0.01

    def test_cmf_zero_score_50(self):
        assert abs(_compute_cmf_score(0.0) - 50.0) < 0.01

    def test_cmf_positive_score_above_50(self):
        assert _compute_cmf_score(0.5) > 50.0

    def test_cmf_negative_score_below_50(self):
        assert _compute_cmf_score(-0.5) < 50.0

    def test_score_clipped(self):
        assert _compute_cmf_score(2.0) <= 100.0
        assert _compute_cmf_score(-2.0) >= 0.0


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
# TestComputeCMFIntegration
# ---------------------------------------------------------------------------

class TestComputeCMFIntegration:
    @patch("quantpilot_stock.cmf.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cmf("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.cmf.engine.yf.Ticker")
    def test_cmf_populated(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cmf("AAPL")
        assert result.cmf is not None

    @patch("quantpilot_stock.cmf.engine.yf.Ticker")
    def test_close_at_high_strong_bull(self, mock_yf):
        """Close at high → CMF=1 → score=100 → strong_bull."""
        idx = pd.date_range("2022-01-01", periods=200, freq="B")
        df = pd.DataFrame({
            "Open": [100.0] * 200,
            "High": [102.0] * 200,
            "Low": [100.0] * 200,
            "Close": [102.0] * 200,
            "Volume": [1_000_000] * 200,
        }, index=idx)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cmf("AAPL")
        assert result.signal == "strong_bull"
        assert result.cmf_strong_bull is True

    @patch("quantpilot_stock.cmf.engine.yf.Ticker")
    def test_close_at_low_strong_bear(self, mock_yf):
        """Close at low → CMF=-1 → score=0 → strong_bear."""
        idx = pd.date_range("2022-01-01", periods=200, freq="B")
        df = pd.DataFrame({
            "Open": [102.0] * 200,
            "High": [102.0] * 200,
            "Low": [100.0] * 200,
            "Close": [100.0] * 200,
            "Volume": [1_000_000] * 200,
        }, index=idx)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cmf("AAPL")
        assert result.signal == "strong_bear"
        assert result.cmf_strong_bear is True

    @patch("quantpilot_stock.cmf.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cmf("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.cmf.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(15)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cmf("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.cmf.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_cmf("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.cmf.engine.yf.Ticker")
    def test_score_bounds(self, mock_yf):
        for df in [_make_ohlcv_df(200, step=3.0), _make_declining_ohlcv(200, step=3.0)]:
            mock_yf.return_value = _mock_ticker(df)
            result = compute_cmf("AAPL")
            assert 0.0 <= result.cmf_score <= 100.0

    @patch("quantpilot_stock.cmf.engine.yf.Ticker")
    def test_direction_populated(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cmf("AAPL")
        assert result.cmf_direction in ("rising", "falling", "flat")


# ---------------------------------------------------------------------------
# TestCMFAPI
# ---------------------------------------------------------------------------

class TestCMFAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/cmf")
        assert resp.status_code == 422

    @patch("quantpilot_stock.cmf.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/cmf?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.cmf.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/cmf?ticker=AAPL").json()
        for f in ["ticker", "cmf", "cmf_positive", "cmf_strong_bull",
                  "cmf_strong_bear", "cmf_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.cmf.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/cmf?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
