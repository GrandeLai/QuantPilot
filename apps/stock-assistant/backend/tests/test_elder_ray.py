"""Tests for Elder Ray Index — Phase F.62.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.elder_ray.engine import (
    _classify_signal,
    _compute_elder_ray_score,
    _compute_elder_ray_series,
    compute_elder_ray,
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
# TestComputeElderRaySeries
# ---------------------------------------------------------------------------

class TestComputeElderRaySeries:
    def test_returns_three_series(self):
        df = _make_ohlcv_df(200)
        result = _compute_elder_ray_series(df["High"], df["Low"], df["Close"])
        assert len(result) == 3

    def test_lengths_match_input(self):
        df = _make_ohlcv_df(200)
        bp, br, ema = _compute_elder_ray_series(df["High"], df["Low"], df["Close"])
        assert len(bp) == len(br) == len(ema) == 200

    def test_rising_stock_positive_bull_power(self):
        """Rising stock: High > EMA(13) → Bull Power > 0."""
        df = _make_ohlcv_df(200, step=1.0)
        bp, _, _ = _compute_elder_ray_series(df["High"], df["Low"], df["Close"])
        assert float(bp.iloc[-1]) > 0.0

    def test_declining_stock_negative_bear_power(self):
        """Declining stock: Low < EMA(13) → Bear Power < 0."""
        df = _make_declining_df(200, step=0.3)
        _, br, _ = _compute_elder_ray_series(df["High"], df["Low"], df["Close"])
        assert float(br.iloc[-1]) < 0.0

    def test_ema_between_low_and_high(self):
        """EMA should generally be within reasonable range of prices."""
        df = _make_ohlcv_df(200)
        _, _, ema = _compute_elder_ray_series(df["High"], df["Low"], df["Close"])
        ema_val = float(ema.iloc[-1])
        last_close = float(df["Close"].iloc[-1])
        # EMA should be within 20% of last close for a monotone trend
        assert abs(ema_val - last_close) / last_close < 0.20

    def test_no_nan_at_end(self):
        df = _make_ohlcv_df(200)
        bp, br, ema = _compute_elder_ray_series(df["High"], df["Low"], df["Close"])
        import math
        assert math.isfinite(float(bp.iloc[-1]))
        assert math.isfinite(float(br.iloc[-1]))
        assert math.isfinite(float(ema.iloc[-1]))


# ---------------------------------------------------------------------------
# TestComputeElderRayScore
# ---------------------------------------------------------------------------

class TestComputeElderRayScore:
    def _make_series(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_all_bullish_high_score(self):
        """Bull > 0, Bear rising, top of distribution → high score."""
        series = self._make_series(list(range(1, 101)))  # 1..100
        score = _compute_elder_ray_score(5.0, -1.0, -2.0, series)
        assert score >= 60.0

    def test_all_bearish_low_score(self):
        """Bull < 0, Bear falling, bottom of distribution → low score."""
        series = self._make_series(list(range(-50, 0)))
        score = _compute_elder_ray_score(-5.0, -10.0, -8.0, series)
        assert score < 40.0

    def test_score_in_range(self):
        series = self._make_series([float(i) for i in range(100)])
        for bull, bear, prev in [(-2.0, -3.0, -4.0), (2.0, -1.0, -2.0)]:
            score = _compute_elder_ray_score(bull, bear, prev, series)
            assert 0.0 <= score <= 100.0

    def test_short_series_fallback(self):
        series = self._make_series([1.0, 2.0])
        score = _compute_elder_ray_score(1.0, -1.0, -2.0, series)
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
# TestComputeElderRayIntegration
# ---------------------------------------------------------------------------

class TestComputeElderRayIntegration:
    @patch("quantpilot_stock.elder_ray.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_elder_ray("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.elder_ray.engine.yf.Ticker")
    def test_components_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_elder_ray("AAPL")
        assert result.bull_power is not None
        assert result.bear_power is not None
        assert result.ema13 is not None

    @patch("quantpilot_stock.elder_ray.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_elder_ray("AAPL")
        assert 0.0 <= result.elder_ray_score <= 100.0

    @patch("quantpilot_stock.elder_ray.engine.yf.Ticker")
    def test_rising_stock_bull_positive(self, mock_yf):
        df = _make_ohlcv_df(300, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_elder_ray("AAPL")
        assert result.bull_positive is True

    @patch("quantpilot_stock.elder_ray.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_elder_ray("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.elder_ray.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(5)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_elder_ray("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.elder_ray.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_elder_ray("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.elder_ray.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_elder_ray("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}

    @patch("quantpilot_stock.elder_ray.engine.yf.Ticker")
    def test_bear_rising_is_bool(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_elder_ray("AAPL")
        assert isinstance(result.bear_rising, bool)


# ---------------------------------------------------------------------------
# TestElderRayAPI
# ---------------------------------------------------------------------------

class TestElderRayAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/elder_ray")
        assert resp.status_code == 422

    @patch("quantpilot_stock.elder_ray.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/elder_ray?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.elder_ray.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/elder_ray?ticker=AAPL").json()
        for f in ["ticker", "bull_power", "bear_power", "ema13",
                  "elder_ray_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.elder_ray.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/elder_ray?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
