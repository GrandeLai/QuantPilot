"""Tests for Chande Kroll Stop (CKS) — Phase F.72.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.cks.engine import (
    _classify_signal,
    _compute_atr,
    _compute_cks_score,
    _compute_cks_series,
    compute_cks,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv_df(n: int, start: float = 100.0, step: float = 0.5) -> pd.DataFrame:
    idx    = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [start + i * step for i in range(n)]
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


def _make_declining_df(n: int, start: float = 200.0, step: float = 0.5) -> pd.DataFrame:
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
# TestComputeATR
# ---------------------------------------------------------------------------

class TestComputeATR:
    def test_positive_values(self):
        df  = _make_ohlcv_df(50)
        atr = _compute_atr(df["High"], df["Low"], df["Close"], 14)
        assert all(v >= 0 for v in atr.dropna())

    def test_constant_range_positive_atr(self):
        """H−L = 2.0 constant → ATR ≈ 2.0."""
        df  = _make_ohlcv_df(50)
        atr = _compute_atr(df["High"], df["Low"], df["Close"], 14)
        assert abs(float(atr.iloc[-1]) - 2.0) < 0.5

    def test_length_matches_input(self):
        df  = _make_ohlcv_df(100)
        atr = _compute_atr(df["High"], df["Low"], df["Close"], 14)
        assert len(atr) == 100


# ---------------------------------------------------------------------------
# TestComputeCKSSeries
# ---------------------------------------------------------------------------

class TestComputeCKSSeries:
    def test_returns_two_series(self):
        df = _make_ohlcv_df(200)
        result = _compute_cks_series(df["High"], df["Low"], df["Close"])
        assert len(result) == 2

    def test_lengths_match_input(self):
        df = _make_ohlcv_df(200)
        stop_s, stop_l = _compute_cks_series(df["High"], df["Low"], df["Close"])
        assert len(stop_s) == len(stop_l) == 200

    def test_stop_short_below_high(self):
        """Bull stop (stop_short) should be below the high most of the time."""
        df = _make_ohlcv_df(200, step=0.0)  # flat price
        stop_s, _ = _compute_cks_series(df["High"], df["Low"], df["Close"])
        assert float(stop_s.iloc[-1]) <= float(df["High"].iloc[-1]) + 0.01

    def test_stop_long_above_low(self):
        """Bear stop (stop_long) should be above the low most of the time."""
        df = _make_ohlcv_df(200, step=0.0)
        _, stop_l = _compute_cks_series(df["High"], df["Low"], df["Close"])
        assert float(stop_l.iloc[-1]) >= float(df["Low"].iloc[-1]) - 0.01

    def test_no_nan_at_end(self):
        df = _make_ohlcv_df(200)
        stop_s, stop_l = _compute_cks_series(df["High"], df["Low"], df["Close"])
        assert stop_s.iloc[-1] == stop_s.iloc[-1]
        assert stop_l.iloc[-1] == stop_l.iloc[-1]

    def test_rising_trend_stop_below_close(self):
        """In a rising trend, bull stop should be below close."""
        df = _make_ohlcv_df(200, step=1.0)
        stop_s, _ = _compute_cks_series(df["High"], df["Low"], df["Close"])
        assert float(stop_s.iloc[-1]) < float(df["Close"].iloc[-1])

    def test_declining_trend_stop_above_close(self):
        """In a declining trend, bear stop should be above close."""
        df = _make_declining_df(200, step=1.0)
        _, stop_l = _compute_cks_series(df["High"], df["Low"], df["Close"])
        assert float(stop_l.iloc[-1]) > float(df["Close"].iloc[-1])

    def test_no_inf_values(self):
        import math
        df = _make_ohlcv_df(200)
        stop_s, stop_l = _compute_cks_series(df["High"], df["Low"], df["Close"])
        for s in (stop_s, stop_l):
            assert all(math.isfinite(v) for v in s.dropna())


# ---------------------------------------------------------------------------
# TestComputeCKSScore
# ---------------------------------------------------------------------------

class TestComputeCKSScore:
    def _make_series(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_price_above_stop_gets_points(self):
        close_s  = self._make_series([110.0] * 100)
        stop_s_s = self._make_series([100.0] * 100)
        score    = _compute_cks_score(110.0, 100.0, stop_s_s, close_s)
        assert score >= 40.0

    def test_price_below_stop_no_above_points(self):
        close_s  = self._make_series([90.0] * 100)
        stop_s_s = self._make_series([100.0] * 100)
        score    = _compute_cks_score(90.0, 100.0, stop_s_s, close_s)
        assert score < 40.0

    def test_score_in_range(self):
        close_s  = self._make_series([100.0] * 100)
        stop_s_s = self._make_series([95.0] * 100)
        for c, s in [(110.0, 100.0), (90.0, 100.0)]:
            score = _compute_cks_score(c, s, stop_s_s, close_s)
            assert 0.0 <= score <= 100.0

    def test_short_series_fallback(self):
        close_s  = self._make_series([100.0, 101.0])
        stop_s_s = self._make_series([98.0, 99.0])
        score    = _compute_cks_score(101.0, 99.0, stop_s_s, close_s)
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

    def test_boundary_20(self):
        assert _classify_signal(20.0) == "bear"


# ---------------------------------------------------------------------------
# TestComputeCKSIntegration
# ---------------------------------------------------------------------------

class TestComputeCKSIntegration:
    @patch("quantpilot_stock.cks.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cks("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.cks.engine.yf.Ticker")
    def test_fields_populated(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cks("AAPL")
        assert result.stop_short is not None
        assert result.stop_long is not None
        assert result.close_value is not None
        assert isinstance(result.price_above_stop, bool)
        assert isinstance(result.stop_rising, bool)

    @patch("quantpilot_stock.cks.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cks("AAPL")
        assert 0.0 <= result.cks_score <= 100.0

    @patch("quantpilot_stock.cks.engine.yf.Ticker")
    def test_rising_stock_above_stop(self, mock_yf):
        df = _make_ohlcv_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cks("AAPL")
        assert result.price_above_stop is True

    @patch("quantpilot_stock.cks.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cks("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}

    @patch("quantpilot_stock.cks.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cks("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.cks.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(5)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cks("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.cks.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_cks("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"


# ---------------------------------------------------------------------------
# TestCKSAPI
# ---------------------------------------------------------------------------

class TestCKSAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/cks")
        assert resp.status_code == 422

    @patch("quantpilot_stock.cks.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/cks?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.cks.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/cks?ticker=AAPL").json()
        for f in ["ticker", "stop_short", "stop_long", "close_value",
                  "price_above_stop", "stop_rising", "cks_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.cks.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/cks?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
