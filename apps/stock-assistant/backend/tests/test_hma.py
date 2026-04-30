"""Tests for Hull Moving Average (HMA) — Phase F.69.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.hma.engine import (
    _classify_signal,
    _compute_hma_score,
    _compute_hma_series,
    _wma,
    compute_hma,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv_df(
    n: int,
    start: float = 100.0,
    step: float = 0.5,
) -> pd.DataFrame:
    idx    = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [start + i * step for i in range(n)]
    return pd.DataFrame(
        {
            "Open":  closes,
            "High":  [c + 1.0 for c in closes],
            "Low":   [c - 1.0 for c in closes],
            "Close": closes,
            "Volume": [1_000_000] * n,
        },
        index=idx,
    )


def _make_declining_df(n: int, start: float = 200.0, step: float = 0.5) -> pd.DataFrame:
    idx    = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [start - i * step for i in range(n)]
    return pd.DataFrame(
        {
            "Open":  closes,
            "High":  [c + 1.0 for c in closes],
            "Low":   [c - 1.0 for c in closes],
            "Close": closes,
            "Volume": [1_000_000] * n,
        },
        index=idx,
    )


def _mock_ticker(df: pd.DataFrame) -> MagicMock:
    tk = MagicMock()
    tk.history.return_value = df
    return tk


# ---------------------------------------------------------------------------
# TestWMA
# ---------------------------------------------------------------------------

class TestWMA:
    def test_returns_correct_length(self):
        s = pd.Series([float(i) for i in range(1, 11)])
        result = _wma(s, 3)
        assert len(result) == 10

    def test_constant_series_returns_constant(self):
        s = pd.Series([5.0] * 20)
        result = _wma(s, 5).dropna()
        assert all(abs(v - 5.0) < 1e-9 for v in result)

    def test_increasing_weights(self):
        """WMA should weight recent values more."""
        s = pd.Series([1.0, 1.0, 1.0, 10.0])
        result = _wma(s, 4)
        # weights: 1,2,3,4; sum=10; WMA = (1+2+3+40)/10 = 4.6
        assert abs(float(result.iloc[-1]) - 4.6) < 1e-6


# ---------------------------------------------------------------------------
# TestComputeHMASeries
# ---------------------------------------------------------------------------

class TestComputeHMASeries:
    def test_returns_series(self):
        df = _make_ohlcv_df(200)
        hma = _compute_hma_series(df["Close"], period=20)
        assert isinstance(hma, pd.Series)

    def test_length_matches_input(self):
        df = _make_ohlcv_df(200)
        hma = _compute_hma_series(df["Close"], period=20)
        assert len(hma) == 200

    def test_no_nan_after_warmup(self):
        df = _make_ohlcv_df(200)
        hma = _compute_hma_series(df["Close"], period=20)
        # After the initial warmup, HMA should not be NaN
        assert hma.iloc[-1] == hma.iloc[-1]  # not NaN

    def test_rising_price_hma_below_close(self):
        """For strongly rising prices, HMA should lag below close."""
        df = _make_ohlcv_df(200, step=2.0)
        hma = _compute_hma_series(df["Close"], period=20)
        # HMA is a moving average, so for rising prices it should be ≤ close eventually
        assert float(hma.iloc[-1]) <= float(df["Close"].iloc[-1]) + 5.0

    def test_hma_lags_in_rising_market(self):
        """For rising prices, HMA should lag — i.e. be below close at end."""
        df  = _make_ohlcv_df(200, start=100.0, step=1.0)
        hma = _compute_hma_series(df["Close"], period=20)
        assert float(hma.iloc[-1]) < float(df["Close"].iloc[-1])

    def test_hma_lags_in_declining_market(self):
        """For declining prices, HMA should lag — i.e. be above close at end."""
        df  = _make_declining_df(200, start=200.0, step=1.0)
        hma = _compute_hma_series(df["Close"], period=20)
        assert float(hma.iloc[-1]) > float(df["Close"].iloc[-1])

    def test_no_inf_values(self):
        import math
        df = _make_ohlcv_df(200)
        hma = _compute_hma_series(df["Close"], period=20)
        assert all(math.isfinite(v) for v in hma.dropna())

    def test_custom_period(self):
        df  = _make_ohlcv_df(200)
        h10 = _compute_hma_series(df["Close"], period=10)
        h50 = _compute_hma_series(df["Close"], period=50)
        # Both should return valid series
        assert len(h10) == 200
        assert len(h50) == 200

    def test_rising_hma_slope(self):
        """HMA of steadily rising data should have positive slope."""
        df  = _make_ohlcv_df(200, step=1.0)
        hma = _compute_hma_series(df["Close"], period=20)
        assert float(hma.iloc[-1]) > float(hma.iloc[-4])


# ---------------------------------------------------------------------------
# TestComputeHMAScore
# ---------------------------------------------------------------------------

class TestComputeHMAScore:
    def _make_series(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_price_above_hma_gets_points(self):
        close_s = self._make_series([100.0 + i for i in range(100)])
        hma_s   = self._make_series([90.0 + i for i in range(100)])
        score   = _compute_hma_score(110.0, 100.0, hma_s, close_s)
        assert score >= 40.0

    def test_price_below_hma_no_above_points(self):
        close_s = self._make_series([90.0 - i * 0.1 for i in range(100)])
        hma_s   = self._make_series([100.0] * 100)
        score   = _compute_hma_score(85.0, 100.0, hma_s, close_s)
        assert score < 40.0

    def test_score_in_range(self):
        close_s = self._make_series([100.0] * 100)
        hma_s   = self._make_series([100.0] * 100)
        for c, h in [(110.0, 100.0), (90.0, 100.0)]:
            score = _compute_hma_score(c, h, hma_s, close_s)
            assert 0.0 <= score <= 100.0

    def test_short_series_fallback(self):
        close_s = self._make_series([100.0, 101.0, 102.0])
        hma_s   = self._make_series([99.0, 100.0, 101.0])
        score   = _compute_hma_score(102.0, 101.0, hma_s, close_s)
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
# TestComputeHMAIntegration
# ---------------------------------------------------------------------------

class TestComputeHMAIntegration:
    @patch("quantpilot_stock.hma.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_hma("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.hma.engine.yf.Ticker")
    def test_fields_populated(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_hma("AAPL")
        assert result.hma_value is not None
        assert result.close_value is not None
        assert isinstance(result.price_above_hma, bool)
        assert isinstance(result.hma_rising, bool)

    @patch("quantpilot_stock.hma.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_hma("AAPL")
        assert 0.0 <= result.hma_score <= 100.0

    @patch("quantpilot_stock.hma.engine.yf.Ticker")
    def test_rising_stock_price_above_hma(self, mock_yf):
        """Steadily rising price should be above HMA (HMA lags)."""
        df = _make_ohlcv_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_hma("AAPL")
        assert result.price_above_hma is True

    @patch("quantpilot_stock.hma.engine.yf.Ticker")
    def test_declining_stock_price_below_hma(self, mock_yf):
        """Steadily declining price should be below HMA."""
        df = _make_declining_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_hma("AAPL")
        assert result.price_above_hma is False

    @patch("quantpilot_stock.hma.engine.yf.Ticker")
    def test_rising_stock_hma_rising(self, mock_yf):
        """Steadily rising price should have a rising HMA."""
        df = _make_ohlcv_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_hma("AAPL")
        assert result.hma_rising is True

    @patch("quantpilot_stock.hma.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_hma("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.hma.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_hma("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}

    @patch("quantpilot_stock.hma.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_hma("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.hma.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_hma("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"


# ---------------------------------------------------------------------------
# TestHMAAPI
# ---------------------------------------------------------------------------

class TestHMAAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/hma")
        assert resp.status_code == 422

    @patch("quantpilot_stock.hma.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/hma?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.hma.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/hma?ticker=AAPL").json()
        for f in ["ticker", "hma_value", "close_value", "price_above_hma",
                  "hma_rising", "hma_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.hma.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/hma?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
