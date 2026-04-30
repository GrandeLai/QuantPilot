"""Tests for Chaikin Oscillator — Phase F.61.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.chaikin_osc.engine import (
    _classify_signal,
    _compute_chaikin_osc_series,
    _compute_chaikin_score,
    compute_chaikin_osc,
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
# TestComputeChaikinOscSeries
# ---------------------------------------------------------------------------

class TestComputeChaikinOscSeries:
    def test_length_matches_input(self):
        df = _make_ohlcv_df(200)
        osc = _compute_chaikin_osc_series(df["High"], df["Low"], df["Close"], df["Volume"])
        assert len(osc) == 200

    def test_returns_series(self):
        df = _make_ohlcv_df(200)
        osc = _compute_chaikin_osc_series(df["High"], df["Low"], df["Close"], df["Volume"])
        assert isinstance(osc, pd.Series)

    def test_no_inf_values(self):
        import math
        df = _make_ohlcv_df(200)
        osc = _compute_chaikin_osc_series(df["High"], df["Low"], df["Close"], df["Volume"])
        assert all(math.isfinite(v) for v in osc.values)

    def test_symmetric_hl_gives_zero_mfm(self):
        """When Close == (High+Low)/2, MFM = 0 → AD is flat → Osc ≈ 0."""
        n   = 100
        idx = pd.date_range("2022-01-01", periods=n, freq="B")
        closes = [100.0] * n
        df = pd.DataFrame({
            "High": [c + 1.0 for c in closes],
            "Low":  [c - 1.0 for c in closes],
            "Close": closes,
            "Volume": [1_000_000] * n,
        }, index=idx)
        osc = _compute_chaikin_osc_series(df["High"], df["Low"], df["Close"], df["Volume"])
        # With constant mid-close the AD line is flat → osc ≈ 0
        assert abs(float(osc.iloc[-1])) < 1e-6

    def test_rising_stock_positive_osc(self):
        """Rising stock: close near high → positive MFM → positive AD → positive osc."""
        n   = 200
        idx = pd.date_range("2022-01-01", periods=n, freq="B")
        closes = [100.0 + i * 1.0 for i in range(n)]
        # close at the high (or very near) → MFM → 1.0
        df = pd.DataFrame({
            "High":   closes,
            "Low":    [c - 2.0 for c in closes],
            "Close":  closes,
            "Volume": [1_000_000] * n,
        }, index=idx)
        osc = _compute_chaikin_osc_series(df["High"], df["Low"], df["Close"], df["Volume"])
        assert float(osc.iloc[-1]) > 0.0

    def test_declining_stock_negative_osc(self):
        """Declining stock: close near low → MFM → -1.0 → negative AD → negative osc."""
        n   = 200
        idx = pd.date_range("2022-01-01", periods=n, freq="B")
        closes = [200.0 - i * 0.5 for i in range(n)]
        df = pd.DataFrame({
            "High":   [c + 2.0 for c in closes],
            "Low":    closes,
            "Close":  closes,
            "Volume": [1_000_000] * n,
        }, index=idx)
        osc = _compute_chaikin_osc_series(df["High"], df["Low"], df["Close"], df["Volume"])
        assert float(osc.iloc[-1]) < 0.0


# ---------------------------------------------------------------------------
# TestComputeChaikinScore
# ---------------------------------------------------------------------------

class TestComputeChaikinScore:
    def _make_series(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_highest_value_high_score(self):
        series = self._make_series([float(i) for i in range(1, 101)])
        assert _compute_chaikin_score(100.0, series) > 90.0

    def test_lowest_value_low_score(self):
        series = self._make_series([float(i) for i in range(1, 101)])
        assert _compute_chaikin_score(0.0, series) < 10.0

    def test_score_in_range(self):
        series = self._make_series([float(i) for i in range(100)])
        assert 0.0 <= _compute_chaikin_score(50.0, series) <= 100.0

    def test_short_series_returns_50(self):
        series = self._make_series([1.0, 2.0, 3.0])
        assert _compute_chaikin_score(2.0, series) == 50.0


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
# TestComputeChaikinOscIntegration
# ---------------------------------------------------------------------------

class TestComputeChaikinOscIntegration:
    @patch("quantpilot_stock.chaikin_osc.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_chaikin_osc("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.chaikin_osc.engine.yf.Ticker")
    def test_osc_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_chaikin_osc("AAPL")
        assert result.chaikin_osc is not None

    @patch("quantpilot_stock.chaikin_osc.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_chaikin_osc("AAPL")
        assert 0.0 <= result.chaikin_score <= 100.0

    @patch("quantpilot_stock.chaikin_osc.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_chaikin_osc("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.chaikin_osc.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(5)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_chaikin_osc("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.chaikin_osc.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_chaikin_osc("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.chaikin_osc.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_chaikin_osc("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}

    @patch("quantpilot_stock.chaikin_osc.engine.yf.Ticker")
    def test_osc_positive_field_bool(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_chaikin_osc("AAPL")
        assert isinstance(result.osc_positive, bool)


# ---------------------------------------------------------------------------
# TestChaikinOscAPI
# ---------------------------------------------------------------------------

class TestChaikinOscAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/chaikin_osc")
        assert resp.status_code == 422

    @patch("quantpilot_stock.chaikin_osc.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/chaikin_osc?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.chaikin_osc.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/chaikin_osc?ticker=AAPL").json()
        for f in ["ticker", "chaikin_osc", "osc_positive", "chaikin_score",
                  "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.chaikin_osc.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/chaikin_osc?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
