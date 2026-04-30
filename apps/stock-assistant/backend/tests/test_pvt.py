"""Tests for Price Volume Trend (PVT) — Phase F.64.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.pvt.engine import (
    _classify_signal,
    _compute_pvt_score,
    _compute_pvt_series,
    compute_pvt,
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
# TestComputePVTSeries
# ---------------------------------------------------------------------------

class TestComputePVTSeries:
    def test_returns_three_series(self):
        df = _make_ohlcv_df(200)
        result = _compute_pvt_series(df["Close"], df["Volume"])
        assert len(result) == 3

    def test_lengths_match_input(self):
        df = _make_ohlcv_df(200)
        pvt, sig, slope = _compute_pvt_series(df["Close"], df["Volume"])
        assert len(pvt) == len(sig) == len(slope) == 200

    def test_rising_stock_positive_slope(self):
        """Rising stock: PVT consistently increases → positive slope."""
        df = _make_ohlcv_df(200, step=1.0)
        _, _, slope = _compute_pvt_series(df["Close"], df["Volume"])
        assert float(slope.iloc[-1]) > 0.0

    def test_declining_stock_negative_slope(self):
        """Declining stock: PVT consistently decreases → negative slope."""
        df = _make_declining_df(200, step=0.3)
        _, _, slope = _compute_pvt_series(df["Close"], df["Volume"])
        assert float(slope.iloc[-1]) < 0.0

    def test_no_inf_values(self):
        import math
        df = _make_ohlcv_df(200)
        pvt, sig, slope = _compute_pvt_series(df["Close"], df["Volume"])
        for s in (pvt, sig, slope):
            assert all(math.isfinite(v) for v in s.values)

    def test_pvt_is_cumulative(self):
        """PVT should grow monotonically for a steadily rising stock."""
        df = _make_ohlcv_df(200, step=1.0)
        pvt, _, _ = _compute_pvt_series(df["Close"], df["Volume"])
        # The last value should be larger than the 50th-percentile value
        assert float(pvt.iloc[-1]) > float(pvt.iloc[100])


# ---------------------------------------------------------------------------
# TestComputePVTScore
# ---------------------------------------------------------------------------

class TestComputePVTScore:
    def _make_series(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_all_bullish_high_score(self):
        """PVT above signal, positive slope, top of distribution → high score."""
        series = self._make_series(list(range(1, 101)))
        score = _compute_pvt_score(100.0, 80.0, 100.0, series)
        assert score >= 60.0

    def test_all_bearish_low_score(self):
        """PVT below signal, negative slope, bottom of distribution → low score."""
        series = self._make_series(list(range(-50, 0)))
        score = _compute_pvt_score(80.0, 100.0, -10.0, series)
        assert score < 40.0

    def test_score_in_range(self):
        series = self._make_series([float(i) for i in range(100)])
        for pvt, sig, slope in [(100, 80, 5), (80, 100, -5)]:
            score = _compute_pvt_score(float(pvt), float(sig), float(slope), series)
            assert 0.0 <= score <= 100.0

    def test_short_series_fallback(self):
        series = self._make_series([1.0, 2.0, 3.0])
        score = _compute_pvt_score(100.0, 80.0, 5.0, series)
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
# TestComputePVTIntegration
# ---------------------------------------------------------------------------

class TestComputePVTIntegration:
    @patch("quantpilot_stock.pvt.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_pvt("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.pvt.engine.yf.Ticker")
    def test_fields_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_pvt("AAPL")
        assert isinstance(result.pvt_above_signal, bool)
        assert isinstance(result.pvt_slope_positive, bool)

    @patch("quantpilot_stock.pvt.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_pvt("AAPL")
        assert 0.0 <= result.pvt_score <= 100.0

    @patch("quantpilot_stock.pvt.engine.yf.Ticker")
    def test_rising_stock_positive_slope(self, mock_yf):
        df = _make_ohlcv_df(300, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_pvt("AAPL")
        assert result.pvt_slope_positive is True

    @patch("quantpilot_stock.pvt.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_pvt("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.pvt.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_pvt("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.pvt.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_pvt("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.pvt.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_pvt("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}


# ---------------------------------------------------------------------------
# TestPVTAPI
# ---------------------------------------------------------------------------

class TestPVTAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/pvt")
        assert resp.status_code == 422

    @patch("quantpilot_stock.pvt.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/pvt?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.pvt.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/pvt?ticker=AAPL").json()
        for f in ["ticker", "pvt_above_signal", "pvt_slope_positive",
                  "pvt_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.pvt.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/pvt?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
