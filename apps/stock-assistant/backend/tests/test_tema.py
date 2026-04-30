"""Tests for TEMA — Triple Exponential Moving Average (F.76).

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.tema.engine import (
    _classify_signal,
    _compute_tema_score,
    _compute_tema_series,
    compute_tema,
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
# TestComputeTEMASeries
# ---------------------------------------------------------------------------

class TestComputeTEMASeries:
    def test_returns_series(self):
        df = _make_ohlcv_df(200)
        tema = _compute_tema_series(df["Close"])
        assert isinstance(tema, pd.Series)

    def test_length_matches_input(self):
        df = _make_ohlcv_df(200)
        tema = _compute_tema_series(df["Close"])
        assert len(tema) == 200

    def test_no_nan_at_end(self):
        df = _make_ohlcv_df(200)
        tema = _compute_tema_series(df["Close"])
        assert not pd.isna(tema.iloc[-1])

    def test_rising_market_tema_tracks_price_closely(self):
        """TEMA eliminates lag so it closely tracks price in a linear trend."""
        df = _make_ohlcv_df(200, step=1.0)
        tema = _compute_tema_series(df["Close"])
        close_last = float(df["Close"].iloc[-1])
        tema_last = float(tema.iloc[-1])
        # TEMA should be within a few bars' distance from price (much closer than SMA)
        assert abs(tema_last - close_last) < close_last * 0.05

    def test_declining_market_tema_tracks_price_closely(self):
        """TEMA tracks declining price closely (minimal lag)."""
        df = _make_declining_df(200, step=1.0)
        tema = _compute_tema_series(df["Close"])
        close_last = float(df["Close"].iloc[-1])
        tema_last = float(tema.iloc[-1])
        assert abs(tema_last - close_last) < close_last * 0.05

    def test_no_inf_values(self):
        import math
        df = _make_ohlcv_df(200)
        tema = _compute_tema_series(df["Close"])
        assert all(math.isfinite(v) for v in tema.dropna())

    def test_custom_period(self):
        df = _make_ohlcv_df(200)
        tema10 = _compute_tema_series(df["Close"], period=10)
        tema50 = _compute_tema_series(df["Close"], period=50)
        assert len(tema10) == len(tema50) == 200

    def test_tema_more_responsive_than_dema(self):
        """TEMA reacts faster than DEMA (closer to price) in a rising market."""
        df = _make_ohlcv_df(200, step=1.0)
        close = df["Close"]
        ema1 = close.ewm(span=20, adjust=False).mean()
        ema2 = ema1.ewm(span=20, adjust=False).mean()
        dema = 2.0 * ema1 - ema2
        tema = _compute_tema_series(close, period=20)
        # In a rising market, TEMA should be closer (larger value) than DEMA
        assert float(tema.iloc[-1]) > float(dema.iloc[-1])

    def test_flat_price_tema_equals_price(self):
        """Flat price → TEMA ≈ price."""
        n = 200
        idx = pd.date_range("2022-01-01", periods=n, freq="B")
        close = pd.Series([100.0] * n, index=idx)
        tema = _compute_tema_series(close)
        assert abs(float(tema.iloc[-1]) - 100.0) < 0.01


# ---------------------------------------------------------------------------
# TestComputeTEMAScore
# ---------------------------------------------------------------------------

class TestComputeTEMAScore:
    def _make_series(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_price_above_rising_tema_scores_high(self):
        tema = self._make_series([95.0 + i * 0.1 for i in range(200)])
        close = self._make_series([100.0 + i * 0.2 for i in range(200)])
        score = _compute_tema_score(140.0, 119.0, tema, close)
        assert score >= 60.0

    def test_price_below_falling_tema_scores_low(self):
        tema = self._make_series([100.0 - i * 0.1 for i in range(200)])
        close = self._make_series([80.0 - i * 0.2 for i in range(200)])
        score = _compute_tema_score(60.0, 80.0, tema, close)
        assert score < 40.0

    def test_score_in_range(self):
        tema = self._make_series([100.0] * 200)
        close = self._make_series([105.0] * 200)
        score = _compute_tema_score(105.0, 100.0, tema, close)
        assert 0.0 <= score <= 100.0

    def test_short_series_fallback(self):
        tema = self._make_series([100.0, 101.0])
        close = self._make_series([102.0, 103.0])
        score = _compute_tema_score(103.0, 101.0, tema, close)
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
# TestComputeTEMAIntegration
# ---------------------------------------------------------------------------

class TestComputeTEMAIntegration:
    @patch("quantpilot_stock.tema.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_tema("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.tema.engine.yf.Ticker")
    def test_fields_populated(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_tema("AAPL")
        assert result.tema_value is not None
        assert isinstance(result.price_above_tema, bool)
        assert isinstance(result.tema_slope_positive, bool)

    @patch("quantpilot_stock.tema.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_tema("AAPL")
        assert 0.0 <= result.tema_score <= 100.0

    @patch("quantpilot_stock.tema.engine.yf.Ticker")
    def test_rising_stock_slope_positive(self, mock_yf):
        """Rising market → TEMA slope positive (reliable signal)."""
        df = _make_ohlcv_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_tema("AAPL")
        assert result.tema_slope_positive is True

    @patch("quantpilot_stock.tema.engine.yf.Ticker")
    def test_declining_stock_slope_negative(self, mock_yf):
        """Declining market → TEMA slope negative (reliable signal)."""
        df = _make_declining_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_tema("AAPL")
        assert result.tema_slope_positive is False

    @patch("quantpilot_stock.tema.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_tema("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}

    @patch("quantpilot_stock.tema.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_tema("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.tema.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_tema("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.tema.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_tema("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.tema.engine.yf.Ticker")
    def test_rising_tema_slope_positive(self, mock_yf):
        df = _make_ohlcv_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_tema("AAPL")
        assert result.tema_slope_positive is True

    @patch("quantpilot_stock.tema.engine.yf.Ticker")
    def test_declining_tema_slope_negative(self, mock_yf):
        df = _make_declining_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_tema("AAPL")
        assert result.tema_slope_positive is False


# ---------------------------------------------------------------------------
# TestTEMAAPI
# ---------------------------------------------------------------------------

class TestTEMAAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/tema")
        assert resp.status_code == 422

    @patch("quantpilot_stock.tema.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/tema?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.tema.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/tema?ticker=AAPL").json()
        for f in ["ticker", "tema_value", "price_above_tema", "tema_slope_positive",
                  "tema_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.tema.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/tema?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
