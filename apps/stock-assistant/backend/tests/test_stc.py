"""Tests for Schaff Trend Cycle (STC) — Phase F.71.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.stc.engine import (
    _classify_signal,
    _compute_stc_score,
    _compute_stc_series,
    _stoch,
    compute_stc,
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
# TestStoch
# ---------------------------------------------------------------------------

class TestStoch:
    def test_constant_series_returns_50(self):
        s = pd.Series([100.0] * 20)
        result = _stoch(s, 10).dropna()
        assert all(abs(v - 50.0) < 1e-6 for v in result)

    def test_at_high_returns_100(self):
        """When value equals rolling high, Stochastic should be 100."""
        # monotone rising — last value is always the max
        s      = pd.Series([float(i) for i in range(1, 21)])
        result = _stoch(s, 10)
        assert abs(float(result.iloc[-1]) - 100.0) < 1e-6

    def test_at_low_returns_0(self):
        """When value equals rolling low, Stochastic should be 0."""
        s      = pd.Series([float(i) for i in range(20, 0, -1)])
        result = _stoch(s, 10)
        assert abs(float(result.iloc[-1]) - 0.0) < 1e-6

    def test_output_range(self):
        import math
        s      = pd.Series([math.sin(i * 0.3) * 10 + 100 for i in range(50)])
        result = _stoch(s, 14)
        assert all(0.0 <= v <= 100.0 for v in result.dropna())


# ---------------------------------------------------------------------------
# TestComputeSTCSeries
# ---------------------------------------------------------------------------

class TestComputeSTCSeries:
    def test_returns_series(self):
        df  = _make_ohlcv_df(200)
        stc = _compute_stc_series(df["Close"])
        assert isinstance(stc, pd.Series)

    def test_length_matches_input(self):
        df  = _make_ohlcv_df(200)
        stc = _compute_stc_series(df["Close"])
        assert len(stc) == 200

    def test_output_range(self):
        df  = _make_ohlcv_df(200)
        stc = _compute_stc_series(df["Close"])
        assert all(0.0 <= v <= 100.0 for v in stc)

    def test_no_nan(self):
        df  = _make_ohlcv_df(200)
        stc = _compute_stc_series(df["Close"])
        assert stc.isna().sum() == 0

    def test_bullish_market_stc_not_low(self):
        """Strongly rising market → STC should be ≥ neutral (not bearish)."""
        idx    = pd.date_range("2022-01-01", periods=300, freq="B")
        closes = [100.0] * 100 + [100.0 + i * 2.0 for i in range(200)]
        df = pd.DataFrame({"Close": closes}, index=idx)
        stc = _compute_stc_series(df["Close"])
        assert float(stc.iloc[-1]) >= 50.0

    def test_stc_higher_for_bull_than_bear(self):
        """Bullish series STC should be higher than bearish series STC."""
        idx      = pd.date_range("2022-01-01", periods=200, freq="B")
        bull_cl  = [100.0 + i * 0.5 for i in range(200)]
        bear_cl  = [200.0 - i * 0.5 for i in range(200)]
        stc_bull = _compute_stc_series(pd.Series(bull_cl, index=idx))
        stc_bear = _compute_stc_series(pd.Series(bear_cl, index=idx))
        assert float(stc_bull.iloc[-1]) >= float(stc_bear.iloc[-1])


# ---------------------------------------------------------------------------
# TestComputeSTCScore
# ---------------------------------------------------------------------------

class TestComputeSTCScore:
    def _make_series(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_above_25_gets_points(self):
        series = self._make_series([30.0] * 100)
        score  = _compute_stc_score(30.0, series)
        assert score >= 40.0

    def test_below_25_no_above_points(self):
        series = self._make_series([20.0] * 100)
        score  = _compute_stc_score(20.0, series)
        assert score < 40.0

    def test_score_in_range(self):
        series = self._make_series([50.0] * 100)
        for v in [10.0, 50.0, 90.0]:
            score = _compute_stc_score(v, series)
            assert 0.0 <= score <= 100.0

    def test_short_series_fallback(self):
        series = self._make_series([50.0, 60.0, 70.0])
        score  = _compute_stc_score(70.0, series)
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


# ---------------------------------------------------------------------------
# TestComputeSTCIntegration
# ---------------------------------------------------------------------------

class TestComputeSTCIntegration:
    @patch("quantpilot_stock.stc.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stc("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.stc.engine.yf.Ticker")
    def test_fields_populated(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stc("AAPL")
        assert result.stc_value is not None
        assert isinstance(result.stc_above_buy, bool)
        assert isinstance(result.stc_rising, bool)

    @patch("quantpilot_stock.stc.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stc("AAPL")
        assert 0.0 <= result.stc_score <= 100.0

    @patch("quantpilot_stock.stc.engine.yf.Ticker")
    def test_stc_value_in_range(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stc("AAPL")
        assert 0.0 <= (result.stc_value or 0.0) <= 100.0

    @patch("quantpilot_stock.stc.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stc("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.stc.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stc("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}

    @patch("quantpilot_stock.stc.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stc("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.stc.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_stc("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"


# ---------------------------------------------------------------------------
# TestSTCAPI
# ---------------------------------------------------------------------------

class TestSTCAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/stc")
        assert resp.status_code == 422

    @patch("quantpilot_stock.stc.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/stc?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.stc.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/stc?ticker=AAPL").json()
        for f in ["ticker", "stc_value", "stc_above_buy", "stc_rising",
                  "stc_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.stc.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/stc?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
