"""Tests for Percentage Price Oscillator (PPO) — Phase F.66.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.ppo.engine import (
    _classify_signal,
    _compute_ppo_score,
    _compute_ppo_series,
    compute_ppo,
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
# TestComputePPOSeries
# ---------------------------------------------------------------------------

class TestComputePPOSeries:
    def test_returns_three_series(self):
        df = _make_ohlcv_df(200)
        result = _compute_ppo_series(df["Close"])
        assert len(result) == 3

    def test_lengths_match_input(self):
        df = _make_ohlcv_df(200)
        ppo, sig, hist = _compute_ppo_series(df["Close"])
        assert len(ppo) == len(sig) == len(hist) == 200

    def test_rising_stock_positive_ppo(self):
        """Steadily rising price → fast EMA > slow EMA → PPO > 0."""
        df = _make_ohlcv_df(200, step=1.0)
        ppo, _, _ = _compute_ppo_series(df["Close"])
        assert float(ppo.iloc[-1]) > 0.0

    def test_declining_stock_negative_ppo(self):
        """Steadily declining price → fast EMA < slow EMA → PPO < 0."""
        df = _make_declining_df(200, step=0.5)
        ppo, _, _ = _compute_ppo_series(df["Close"])
        assert float(ppo.iloc[-1]) < 0.0

    def test_histogram_is_ppo_minus_signal(self):
        df = _make_ohlcv_df(200)
        ppo, sig, hist = _compute_ppo_series(df["Close"])
        import math
        assert math.isclose(
            float(ppo.iloc[-1]) - float(sig.iloc[-1]),
            float(hist.iloc[-1]),
            abs_tol=1e-9,
        )

    def test_no_inf_values(self):
        import math
        df = _make_ohlcv_df(200)
        ppo, sig, hist = _compute_ppo_series(df["Close"])
        for s in (ppo, sig, hist):
            assert all(math.isfinite(v) for v in s.values)

    def test_flat_price_zero_ppo(self):
        """Flat price → both EMAs equal → PPO = 0."""
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        closes = pd.Series([100.0] * 100, index=idx)
        ppo, _, _ = _compute_ppo_series(closes)
        assert abs(float(ppo.iloc[-1])) < 1e-9


# ---------------------------------------------------------------------------
# TestComputePPOScore
# ---------------------------------------------------------------------------

class TestComputePPOScore:
    def _make_series(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_all_bullish_high_score(self):
        series = self._make_series([float(i) for i in range(-20, 21)])
        score = _compute_ppo_score(15.0, 10.0, series)
        assert score >= 60.0

    def test_all_bearish_low_score(self):
        series = self._make_series([float(i) for i in range(-20, 0)])
        score = _compute_ppo_score(-10.0, 0.0, series)
        assert score < 40.0

    def test_score_in_range(self):
        series = self._make_series([float(i) for i in range(-20, 21)])
        for ppo, sig in [(5.0, 2.0), (-5.0, -2.0)]:
            score = _compute_ppo_score(ppo, sig, series)
            assert 0.0 <= score <= 100.0

    def test_short_series_fallback(self):
        series = self._make_series([1.0, 2.0, 3.0])
        score = _compute_ppo_score(1.0, 0.5, series)
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
# TestComputePPOIntegration
# ---------------------------------------------------------------------------

class TestComputePPOIntegration:
    @patch("quantpilot_stock.ppo.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ppo("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.ppo.engine.yf.Ticker")
    def test_fields_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ppo("AAPL")
        assert isinstance(result.ppo_above_signal, bool)
        assert isinstance(result.ppo_positive, bool)
        assert result.ppo_value is not None
        assert result.signal_value is not None
        assert result.histogram is not None

    @patch("quantpilot_stock.ppo.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ppo("AAPL")
        assert 0.0 <= result.ppo_score <= 100.0

    @patch("quantpilot_stock.ppo.engine.yf.Ticker")
    def test_rising_stock_positive_ppo(self, mock_yf):
        df = _make_ohlcv_df(300, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ppo("AAPL")
        assert result.ppo_positive is True

    @patch("quantpilot_stock.ppo.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ppo("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.ppo.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ppo("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.ppo.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_ppo("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.ppo.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ppo("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}


# ---------------------------------------------------------------------------
# TestPPOAPI
# ---------------------------------------------------------------------------

class TestPPOAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/ppo")
        assert resp.status_code == 422

    @patch("quantpilot_stock.ppo.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/ppo?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.ppo.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/ppo?ticker=AAPL").json()
        for f in ["ticker", "ppo_value", "signal_value", "histogram",
                  "ppo_above_signal", "ppo_positive", "ppo_score",
                  "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.ppo.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/ppo?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
