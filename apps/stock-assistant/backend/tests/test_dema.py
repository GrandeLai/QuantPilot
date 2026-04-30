"""Tests for DEMA — Double Exponential Moving Average (F.75).

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.dema.engine import (
    _classify_signal,
    _compute_dema_score,
    _compute_dema_series,
    compute_dema,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv_df(
    n: int,
    start: float = 100.0,
    step: float = 0.5,
) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
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
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
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
# TestComputeDEMASeries
# ---------------------------------------------------------------------------

class TestComputeDEMASeries:
    def test_returns_series(self):
        df = _make_ohlcv_df(200)
        dema = _compute_dema_series(df["Close"])
        assert isinstance(dema, pd.Series)

    def test_length_matches_input(self):
        df = _make_ohlcv_df(200)
        dema = _compute_dema_series(df["Close"])
        assert len(dema) == 200

    def test_no_nan_at_end(self):
        df = _make_ohlcv_df(200)
        dema = _compute_dema_series(df["Close"])
        assert not pd.isna(dema.iloc[-1])

    def test_rising_market_dema_below_price(self):
        """In a strongly rising market, DEMA trails price (less lag than EMA but still lags)."""
        df = _make_ohlcv_df(200, step=1.0)
        dema = _compute_dema_series(df["Close"])
        assert float(dema.iloc[-1]) < float(df["Close"].iloc[-1])

    def test_declining_market_dema_above_price(self):
        """In a declining market, DEMA is above price."""
        df = _make_declining_df(200, step=1.0)
        dema = _compute_dema_series(df["Close"])
        assert float(dema.iloc[-1]) > float(df["Close"].iloc[-1])

    def test_no_inf_values(self):
        import math
        df = _make_ohlcv_df(200)
        dema = _compute_dema_series(df["Close"])
        assert all(math.isfinite(v) for v in dema.dropna())

    def test_custom_period(self):
        df = _make_ohlcv_df(200)
        dema10 = _compute_dema_series(df["Close"], period=10)
        dema50 = _compute_dema_series(df["Close"], period=50)
        assert len(dema10) == len(dema50) == 200

    def test_dema_more_responsive_than_ema(self):
        """DEMA reacts faster than plain EMA (closer to price in a trend)."""
        df = _make_ohlcv_df(200, step=1.0)
        close = df["Close"]
        ema = close.ewm(span=20, adjust=False).mean()
        dema = _compute_dema_series(close, period=20)
        # In a rising market, DEMA should be closer (larger) than EMA
        assert float(dema.iloc[-1]) > float(ema.iloc[-1])

    def test_flat_price_dema_equals_price(self):
        """Flat price → DEMA ≈ price."""
        n = 200
        idx = pd.date_range("2022-01-01", periods=n, freq="B")
        close = pd.Series([100.0] * n, index=idx)
        dema = _compute_dema_series(close)
        assert abs(float(dema.iloc[-1]) - 100.0) < 0.01


# ---------------------------------------------------------------------------
# TestComputeDEMAScore
# ---------------------------------------------------------------------------

class TestComputeDEMAScore:
    def _make_series(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_price_above_rising_dema_scores_high(self):
        dema = self._make_series([95.0 + i * 0.1 for i in range(200)])
        close = self._make_series([100.0 + i * 0.2 for i in range(200)])
        score = _compute_dema_score(5.0, 140.0, 119.0, dema, close)
        assert score >= 60.0

    def test_price_below_falling_dema_scores_low(self):
        dema = self._make_series([100.0 - i * 0.1 for i in range(200)])
        close = self._make_series([80.0 - i * 0.2 for i in range(200)])
        score = _compute_dema_score(-20.0, 60.0, 80.0, dema, close)
        assert score < 40.0

    def test_score_in_range(self):
        dema = self._make_series([100.0] * 200)
        close = self._make_series([105.0] * 200)
        score = _compute_dema_score(5.0, 105.0, 100.0, dema, close)
        assert 0.0 <= score <= 100.0

    def test_short_series_fallback(self):
        dema = self._make_series([100.0, 101.0])
        close = self._make_series([102.0, 103.0])
        score = _compute_dema_score(2.0, 103.0, 101.0, dema, close)
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
# TestComputeDEMAIntegration
# ---------------------------------------------------------------------------

class TestComputeDEMAIntegration:
    @patch("quantpilot_stock.dema.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_dema("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.dema.engine.yf.Ticker")
    def test_fields_populated(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_dema("AAPL")
        assert result.dema_value is not None
        assert isinstance(result.price_above_dema, bool)
        assert isinstance(result.dema_slope_positive, bool)

    @patch("quantpilot_stock.dema.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_dema("AAPL")
        assert 0.0 <= result.dema_score <= 100.0

    @patch("quantpilot_stock.dema.engine.yf.Ticker")
    def test_rising_stock_price_above_dema(self, mock_yf):
        df = _make_ohlcv_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_dema("AAPL")
        assert result.price_above_dema is True

    @patch("quantpilot_stock.dema.engine.yf.Ticker")
    def test_declining_stock_price_below_dema(self, mock_yf):
        df = _make_declining_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_dema("AAPL")
        assert result.price_above_dema is False

    @patch("quantpilot_stock.dema.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_dema("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}

    @patch("quantpilot_stock.dema.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_dema("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.dema.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_dema("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.dema.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_dema("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.dema.engine.yf.Ticker")
    def test_rising_dema_slope_positive(self, mock_yf):
        df = _make_ohlcv_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_dema("AAPL")
        assert result.dema_slope_positive is True

    @patch("quantpilot_stock.dema.engine.yf.Ticker")
    def test_declining_dema_slope_negative(self, mock_yf):
        df = _make_declining_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_dema("AAPL")
        assert result.dema_slope_positive is False


# ---------------------------------------------------------------------------
# TestDEMAAPI
# ---------------------------------------------------------------------------

class TestDEMAAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/dema")
        assert resp.status_code == 422

    @patch("quantpilot_stock.dema.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/dema?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.dema.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/dema?ticker=AAPL").json()
        for f in ["ticker", "dema_value", "price_above_dema", "dema_slope_positive",
                  "dema_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.dema.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/dema?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
