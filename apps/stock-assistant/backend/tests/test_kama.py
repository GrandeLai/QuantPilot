"""Tests for Kaufman Adaptive Moving Average (KAMA) — Phase F.70.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.kama.engine import (
    _classify_signal,
    _compute_kama_score,
    _compute_kama_series,
    compute_kama,
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


def _make_noisy_df(n: int, base: float = 100.0, noise: float = 2.0) -> pd.DataFrame:
    """Sideways noisy price — low efficiency ratio."""
    import math
    idx    = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [base + noise * math.sin(i * 0.5) for i in range(n)]
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
# TestComputeKAMASeries
# ---------------------------------------------------------------------------

class TestComputeKAMASeries:
    def test_returns_series(self):
        df = _make_ohlcv_df(200)
        kama = _compute_kama_series(df["Close"])
        assert isinstance(kama, pd.Series)

    def test_length_matches_input(self):
        df = _make_ohlcv_df(200)
        kama = _compute_kama_series(df["Close"])
        assert len(kama) == 200

    def test_no_nan_at_end(self):
        df   = _make_ohlcv_df(200)
        kama = _compute_kama_series(df["Close"])
        assert kama.iloc[-1] == kama.iloc[-1]  # not NaN

    def test_rising_price_kama_below_close(self):
        """For strongly rising prices, KAMA lags behind close."""
        df   = _make_ohlcv_df(200, step=2.0)
        kama = _compute_kama_series(df["Close"])
        assert float(kama.iloc[-1]) <= float(df["Close"].iloc[-1])

    def test_declining_price_kama_above_close(self):
        """For declining prices, KAMA lags above close."""
        df   = _make_declining_df(200, step=2.0)
        kama = _compute_kama_series(df["Close"])
        assert float(kama.iloc[-1]) >= float(df["Close"].iloc[-1])

    def test_no_inf_values(self):
        import math
        df   = _make_ohlcv_df(200)
        kama = _compute_kama_series(df["Close"])
        assert all(math.isfinite(v) for v in kama.dropna())

    def test_sideways_market_kama_slow(self):
        """In sideways/noisy market, KAMA should barely move (low ER)."""
        df     = _make_noisy_df(200)
        kama   = _compute_kama_series(df["Close"])
        # range of KAMA should be much smaller than range of close
        kama_range  = float(kama.max() - kama.min())
        close_range = float(df["Close"].max() - df["Close"].min())
        assert kama_range < close_range

    def test_trending_market_kama_follows_closely(self):
        """In strongly trending market, KAMA should track close closely."""
        df   = _make_ohlcv_df(200, step=3.0)
        kama = _compute_kama_series(df["Close"])
        # KAMA should be within reasonable distance of final close
        gap = abs(float(kama.iloc[-1]) - float(df["Close"].iloc[-1]))
        assert gap < 60.0  # less than 60 price units of lag

    def test_custom_period(self):
        df    = _make_ohlcv_df(200)
        k5    = _compute_kama_series(df["Close"], period=5)
        k20   = _compute_kama_series(df["Close"], period=20)
        assert len(k5) == len(k20) == 200


# ---------------------------------------------------------------------------
# TestComputeKAMAScore
# ---------------------------------------------------------------------------

class TestComputeKAMAScore:
    def _make_series(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_price_above_kama_gets_points(self):
        close_s = self._make_series([100.0 + i * 0.5 for i in range(100)])
        kama_s  = self._make_series([90.0 + i * 0.5 for i in range(100)])
        score   = _compute_kama_score(110.0, 100.0, kama_s, close_s)
        assert score >= 40.0

    def test_price_below_kama_no_above_points(self):
        close_s = self._make_series([90.0 - i * 0.1 for i in range(100)])
        kama_s  = self._make_series([100.0] * 100)
        score   = _compute_kama_score(85.0, 100.0, kama_s, close_s)
        assert score < 40.0

    def test_score_in_range(self):
        close_s = self._make_series([100.0] * 100)
        kama_s  = self._make_series([100.0] * 100)
        for c, k in [(110.0, 100.0), (90.0, 100.0)]:
            score = _compute_kama_score(c, k, kama_s, close_s)
            assert 0.0 <= score <= 100.0

    def test_short_series_fallback(self):
        close_s = self._make_series([100.0, 101.0, 102.0])
        kama_s  = self._make_series([99.0, 100.0, 101.0])
        score   = _compute_kama_score(102.0, 101.0, kama_s, close_s)
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
# TestComputeKAMAIntegration
# ---------------------------------------------------------------------------

class TestComputeKAMAIntegration:
    @patch("quantpilot_stock.kama.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_kama("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.kama.engine.yf.Ticker")
    def test_fields_populated(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_kama("AAPL")
        assert result.kama_value is not None
        assert result.close_value is not None
        assert isinstance(result.price_above_kama, bool)
        assert isinstance(result.kama_rising, bool)

    @patch("quantpilot_stock.kama.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_kama("AAPL")
        assert 0.0 <= result.kama_score <= 100.0

    @patch("quantpilot_stock.kama.engine.yf.Ticker")
    def test_rising_stock_price_above_kama(self, mock_yf):
        df = _make_ohlcv_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_kama("AAPL")
        assert result.price_above_kama is True

    @patch("quantpilot_stock.kama.engine.yf.Ticker")
    def test_declining_stock_price_below_kama(self, mock_yf):
        df = _make_declining_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_kama("AAPL")
        assert result.price_above_kama is False

    @patch("quantpilot_stock.kama.engine.yf.Ticker")
    def test_rising_stock_kama_rising(self, mock_yf):
        df = _make_ohlcv_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_kama("AAPL")
        assert result.kama_rising is True

    @patch("quantpilot_stock.kama.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_kama("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.kama.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_kama("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}

    @patch("quantpilot_stock.kama.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_kama("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.kama.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_kama("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"


# ---------------------------------------------------------------------------
# TestKAMAAPI
# ---------------------------------------------------------------------------

class TestKAMAAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/kama")
        assert resp.status_code == 422

    @patch("quantpilot_stock.kama.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/kama?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.kama.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/kama?ticker=AAPL").json()
        for f in ["ticker", "kama_value", "close_value", "price_above_kama",
                  "kama_rising", "kama_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.kama.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/kama?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
