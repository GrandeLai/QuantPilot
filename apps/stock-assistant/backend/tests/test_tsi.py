"""Tests for TSI (True Strength Index) — Phase F.57.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

import math
from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.tsi.engine import (
    _classify_signal,
    _compute_tsi_score,
    _compute_tsi_series,
    compute_tsi,
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
# TestComputeTSISeries
# ---------------------------------------------------------------------------


class TestComputeTSISeries:
    def test_length_matches_input(self):
        df = _make_ohlcv_df(200)
        tsi, sig = _compute_tsi_series(df["Close"])
        assert len(tsi) == len(sig) == 200

    def test_rising_stock_positive_tsi(self):
        df = _make_ohlcv_df(200, step=1.0)
        tsi, _ = _compute_tsi_series(df["Close"])
        assert float(tsi.iloc[-1]) > 0.0

    def test_declining_stock_negative_tsi(self):
        df = _make_declining_df(200, step=1.0)
        tsi, _ = _compute_tsi_series(df["Close"])
        assert float(tsi.iloc[-1]) < 0.0

    def test_flat_stock_near_zero(self):
        idx   = pd.date_range("2022-01-01", periods=200, freq="B")
        close = pd.Series([100.0] * 200, index=idx)
        tsi, _ = _compute_tsi_series(close)
        assert abs(float(tsi.iloc[-1])) < 1.0

    def test_tsi_finite(self):
        df = _make_ohlcv_df(200, step=0.5)
        tsi, _ = _compute_tsi_series(df["Close"])
        assert math.isfinite(float(tsi.iloc[-1]))

    def test_signal_finite(self):
        df = _make_ohlcv_df(200, step=0.5)
        _, sig = _compute_tsi_series(df["Close"])
        assert math.isfinite(float(sig.iloc[-1]))

    def test_tsi_range(self):
        """TSI should be in [-100, 100] for well-behaved inputs."""
        df = _make_ohlcv_df(200, step=1.0)
        tsi, _ = _compute_tsi_series(df["Close"])
        val = float(tsi.iloc[-1])
        assert -100.0 <= val <= 100.0


# ---------------------------------------------------------------------------
# TestComputeTSIScore
# ---------------------------------------------------------------------------


class TestComputeTSIScore:
    def test_highest_tsi_gives_high_score(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        tsi = pd.Series([0.0] * 99 + [50.0], index=idx)
        assert _compute_tsi_score(50.0, tsi) > 90.0

    def test_lowest_tsi_gives_low_score(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        tsi = pd.Series([0.0] * 99 + [-50.0], index=idx)
        assert _compute_tsi_score(-50.0, tsi) < 10.0

    def test_score_in_range(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        tsi = pd.Series(range(-50, 50), dtype=float, index=idx)
        assert 0.0 <= _compute_tsi_score(0.0, tsi) <= 100.0

    def test_short_series_fallback(self):
        idx = pd.date_range("2022-01-01", periods=5, freq="B")
        tsi = pd.Series([10.0, -10.0, 5.0, -5.0, 0.0], index=idx)
        score = _compute_tsi_score(0.0, tsi)
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
# TestComputeTSIIntegration
# ---------------------------------------------------------------------------


class TestComputeTSIIntegration:
    @patch("quantpilot_stock.tsi.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_tsi("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.tsi.engine.yf.Ticker")
    def test_tsi_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_tsi("AAPL")
        assert result.tsi_value is not None

    @patch("quantpilot_stock.tsi.engine.yf.Ticker")
    def test_signal_line_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_tsi("AAPL")
        assert result.signal_line is not None

    @patch("quantpilot_stock.tsi.engine.yf.Ticker")
    def test_rising_stock_positive_tsi(self, mock_yf):
        df = _make_ohlcv_df(300, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_tsi("AAPL")
        assert result.tsi_positive is True

    @patch("quantpilot_stock.tsi.engine.yf.Ticker")
    def test_declining_stock_negative_tsi(self, mock_yf):
        df = _make_declining_df(300, step=0.3)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_tsi("AAPL")
        assert result.tsi_positive is False

    @patch("quantpilot_stock.tsi.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_tsi("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.tsi.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_tsi("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.tsi.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_tsi("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.tsi.engine.yf.Ticker")
    def test_score_bounds(self, mock_yf):
        for df in [_make_ohlcv_df(300, step=2.0), _make_declining_df(300)]:
            mock_yf.return_value = _mock_ticker(df)
            result = compute_tsi("AAPL")
            assert 0.0 <= result.tsi_score <= 100.0

    @patch("quantpilot_stock.tsi.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_tsi("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}


# ---------------------------------------------------------------------------
# TestTSIAPI
# ---------------------------------------------------------------------------


class TestTSIAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/tsi")
        assert resp.status_code == 422

    @patch("quantpilot_stock.tsi.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/tsi?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.tsi.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/tsi?ticker=AAPL").json()
        for f in ["ticker", "tsi_value", "signal_line", "tsi_positive",
                  "tsi_above_signal", "tsi_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.tsi.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/tsi?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
