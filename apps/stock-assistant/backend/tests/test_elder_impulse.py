"""Tests for Elder Impulse System — F.80.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.elder_impulse.engine import (
    _classify_impulse_color,
    _classify_signal,
    _compute_impulse_score,
    _compute_macd_hist,
    compute_impulse,
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
# TestComputeMACDHist
# ---------------------------------------------------------------------------

class TestComputeMACDHist:
    def test_returns_series(self):
        df = _make_ohlcv_df(200)
        hist = _compute_macd_hist(df["Close"])
        assert isinstance(hist, pd.Series)

    def test_length_matches_input(self):
        df = _make_ohlcv_df(200)
        hist = _compute_macd_hist(df["Close"])
        assert len(hist) == 200

    def test_no_nan_at_end(self):
        df = _make_ohlcv_df(200)
        hist = _compute_macd_hist(df["Close"])
        assert not pd.isna(hist.iloc[-1])

    def test_no_inf_values(self):
        import math
        df = _make_ohlcv_df(200)
        hist = _compute_macd_hist(df["Close"])
        assert all(math.isfinite(v) for v in hist.dropna())


# ---------------------------------------------------------------------------
# TestClassifyImpulseColor
# ---------------------------------------------------------------------------

class TestClassifyImpulseColor:
    def test_green_when_both_rising(self):
        assert _classify_impulse_color(True, True) == "green"

    def test_red_when_both_falling(self):
        assert _classify_impulse_color(False, False) == "red"

    def test_blue_when_mixed_ema_up_hist_down(self):
        assert _classify_impulse_color(True, False) == "blue"

    def test_blue_when_mixed_ema_down_hist_up(self):
        assert _classify_impulse_color(False, True) == "blue"


# ---------------------------------------------------------------------------
# TestComputeImpulseScore
# ---------------------------------------------------------------------------

class TestComputeImpulseScore:
    def _make_series(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_bullish_setup_scores_high(self):
        """Rising EMA + positive rising MACD hist → high score."""
        ema = self._make_series([100.0 + i * 0.1 for i in range(200)])
        hist = self._make_series([0.1 + i * 0.001 for i in range(200)])
        close = self._make_series([105.0 + i * 0.2 for i in range(200)])
        score = _compute_impulse_score(145.0, 120.0, ema, hist, close)
        assert score >= 60.0

    def test_bearish_setup_scores_low(self):
        """Falling EMA + negative falling MACD hist → low score."""
        ema = self._make_series([100.0 - i * 0.1 for i in range(200)])
        hist = self._make_series([-0.1 - i * 0.001 for i in range(200)])
        close = self._make_series([90.0 - i * 0.2 for i in range(200)])
        score = _compute_impulse_score(90.0, 80.0, ema, hist, close)
        assert score < 40.0

    def test_score_in_range(self):
        ema = self._make_series([100.0] * 200)
        hist = self._make_series([0.0] * 200)
        close = self._make_series([100.0] * 200)
        score = _compute_impulse_score(100.0, 100.0, ema, hist, close)
        assert 0.0 <= score <= 100.0

    def test_short_series_fallback(self):
        ema = self._make_series([100.0, 101.0])
        hist = self._make_series([0.1, 0.2])
        close = self._make_series([102.0, 103.0])
        score = _compute_impulse_score(103.0, 101.0, ema, hist, close)
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
# TestComputeImpulseIntegration
# ---------------------------------------------------------------------------

class TestComputeImpulseIntegration:
    @patch("quantpilot_stock.elder_impulse.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_impulse("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.elder_impulse.engine.yf.Ticker")
    def test_fields_populated(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_impulse("AAPL")
        assert result.ema13 is not None
        assert result.macd_hist is not None
        assert result.impulse_color in {"green", "red", "blue"}

    @patch("quantpilot_stock.elder_impulse.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_impulse("AAPL")
        assert 0.0 <= result.impulse_score <= 100.0

    @patch("quantpilot_stock.elder_impulse.engine.yf.Ticker")
    def test_rising_market_ema_rising(self, mock_yf):
        """Rising market → EMA(13) must be rising."""
        df = _make_ohlcv_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_impulse("AAPL")
        assert result.ema_rising is True

    @patch("quantpilot_stock.elder_impulse.engine.yf.Ticker")
    def test_declining_market_ema_falling(self, mock_yf):
        """Declining market → EMA(13) must be falling."""
        df = _make_declining_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_impulse("AAPL")
        assert result.ema_rising is False

    @patch("quantpilot_stock.elder_impulse.engine.yf.Ticker")
    def test_impulse_color_valid_values(self, mock_yf):
        """impulse_color must be one of green/red/blue."""
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_impulse("AAPL")
        assert result.impulse_color in {"green", "red", "blue"}

    @patch("quantpilot_stock.elder_impulse.engine.yf.Ticker")
    def test_green_impulse_requires_both_rising(self, mock_yf):
        """Green impulse only when both EMA and hist are rising."""
        df = _make_ohlcv_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_impulse("AAPL")
        if result.impulse_color == "green":
            assert result.ema_rising is True
            assert result.hist_rising is True

    @patch("quantpilot_stock.elder_impulse.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_impulse("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}

    @patch("quantpilot_stock.elder_impulse.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_impulse("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.elder_impulse.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_impulse("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.elder_impulse.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_impulse("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"


# ---------------------------------------------------------------------------
# TestElderImpulseAPI
# ---------------------------------------------------------------------------

class TestElderImpulseAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/elder_impulse")
        assert resp.status_code == 422

    @patch("quantpilot_stock.elder_impulse.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/elder_impulse?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.elder_impulse.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/elder_impulse?ticker=AAPL").json()
        for f in ["ticker", "ema13", "macd_hist", "impulse_color",
                  "ema_rising", "hist_rising", "impulse_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.elder_impulse.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/elder_impulse?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
