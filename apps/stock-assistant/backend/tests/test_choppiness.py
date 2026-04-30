"""Tests for Choppiness Index — F.79.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.choppiness.engine import (
    _classify_signal,
    _compute_chop_score,
    _compute_chop_series,
    compute_chop,
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


def _make_choppy_df(n: int, base: float = 100.0, noise: float = 2.0) -> pd.DataFrame:
    """Oscillating price with large H-L range relative to net movement."""
    import math
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [base + noise * math.sin(i * 0.5) for i in range(n)]
    return pd.DataFrame(
        {
            "Open":   closes,
            "High":   [c + noise for c in closes],
            "Low":    [c - noise for c in closes],
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
# TestComputeChopSeries
# ---------------------------------------------------------------------------

class TestComputeChopSeries:
    def test_returns_series(self):
        df = _make_ohlcv_df(200)
        chop = _compute_chop_series(df["High"], df["Low"], df["Close"])
        assert isinstance(chop, pd.Series)

    def test_length_matches_input(self):
        df = _make_ohlcv_df(200)
        chop = _compute_chop_series(df["High"], df["Low"], df["Close"])
        assert len(chop) == 200

    def test_values_in_range(self):
        df = _make_ohlcv_df(200)
        chop = _compute_chop_series(df["High"], df["Low"], df["Close"])
        assert chop.min() >= 0.0
        assert chop.max() <= 100.0

    def test_no_nan_at_end(self):
        df = _make_ohlcv_df(200)
        chop = _compute_chop_series(df["High"], df["Low"], df["Close"])
        assert not pd.isna(chop.iloc[-1])

    def test_trending_market_low_chop(self):
        """Strongly trending market → low Choppiness."""
        df = _make_ohlcv_df(200, step=2.0)
        chop = _compute_chop_series(df["High"], df["Low"], df["Close"])
        assert float(chop.iloc[-1]) < 61.8

    def test_choppy_market_high_chop(self):
        """Sideways oscillating market → high Choppiness."""
        df = _make_choppy_df(200)
        chop = _compute_chop_series(df["High"], df["Low"], df["Close"])
        assert float(chop.iloc[-1]) > 38.2

    def test_custom_period(self):
        df = _make_ohlcv_df(200)
        chop7 = _compute_chop_series(df["High"], df["Low"], df["Close"], period=7)
        chop21 = _compute_chop_series(df["High"], df["Low"], df["Close"], period=21)
        assert len(chop7) == len(chop21) == 200

    def test_no_inf_values(self):
        import math
        df = _make_ohlcv_df(200)
        chop = _compute_chop_series(df["High"], df["Low"], df["Close"])
        assert all(math.isfinite(v) for v in chop.dropna())


# ---------------------------------------------------------------------------
# TestComputeChopScore
# ---------------------------------------------------------------------------

class TestComputeChopScore:
    def _make_series(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_trending_and_price_above_sma_scores_high(self):
        """Low CHOP + price above SMA → high score."""
        chop = self._make_series([35.0] * 200)
        score = _compute_chop_score(35.0, 110.0, 100.0, chop)
        assert score >= 60.0

    def test_choppy_and_price_below_sma_scores_low(self):
        """High CHOP + price below SMA → low score."""
        chop = self._make_series([70.0] * 200)
        score = _compute_chop_score(70.0, 90.0, 100.0, chop)
        assert score < 40.0

    def test_score_in_range(self):
        chop = self._make_series([50.0] * 200)
        score = _compute_chop_score(50.0, 100.0, 100.0, chop)
        assert 0.0 <= score <= 100.0

    def test_short_series_fallback(self):
        chop = self._make_series([40.0, 42.0])
        score = _compute_chop_score(42.0, 105.0, 100.0, chop)
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
# TestComputeChopIntegration
# ---------------------------------------------------------------------------

class TestComputeChopIntegration:
    @patch("quantpilot_stock.choppiness.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_chop("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.choppiness.engine.yf.Ticker")
    def test_fields_populated(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_chop("AAPL")
        assert result.chop_value is not None
        assert isinstance(result.is_trending, bool)
        assert isinstance(result.price_above_sma, bool)

    @patch("quantpilot_stock.choppiness.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_chop("AAPL")
        assert 0.0 <= result.chop_score <= 100.0

    @patch("quantpilot_stock.choppiness.engine.yf.Ticker")
    def test_chop_value_in_range(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_chop("AAPL")
        assert 0.0 <= (result.chop_value or 0.0) <= 100.0

    @patch("quantpilot_stock.choppiness.engine.yf.Ticker")
    def test_trending_market_is_trending_true(self, mock_yf):
        """Strong trend → CHOP < 50 → is_trending=True."""
        df = _make_ohlcv_df(200, step=2.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_chop("AAPL")
        assert result.is_trending is True

    @patch("quantpilot_stock.choppiness.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_chop("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}

    @patch("quantpilot_stock.choppiness.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_chop("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.choppiness.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_chop("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.choppiness.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_chop("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.choppiness.engine.yf.Ticker")
    def test_rising_stock_price_above_sma(self, mock_yf):
        df = _make_ohlcv_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_chop("AAPL")
        assert result.price_above_sma is True


# ---------------------------------------------------------------------------
# TestChoppinessAPI
# ---------------------------------------------------------------------------

class TestChoppinessAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/choppiness")
        assert resp.status_code == 422

    @patch("quantpilot_stock.choppiness.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/choppiness?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.choppiness.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/choppiness?ticker=AAPL").json()
        for f in ["ticker", "chop_value", "is_trending", "price_above_sma",
                  "chop_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.choppiness.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/choppiness?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
