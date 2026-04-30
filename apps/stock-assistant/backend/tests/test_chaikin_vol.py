"""Tests for Chaikin Volatility (CV) — Phase F.74.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.chaikin_vol.engine import (
    _classify_signal,
    _compute_cv_score,
    _compute_cv_series,
    compute_cv,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv_df(
    n: int,
    start: float = 100.0,
    step: float = 0.5,
    hl_spread: float = 2.0,
) -> pd.DataFrame:
    idx    = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [start + i * step for i in range(n)]
    return pd.DataFrame(
        {
            "Open":   closes,
            "High":   [c + hl_spread for c in closes],
            "Low":    [c - hl_spread for c in closes],
            "Close":  closes,
            "Volume": [1_000_000] * n,
        },
        index=idx,
    )


def _make_expanding_hl_df(n: int, base: float = 100.0) -> pd.DataFrame:
    """HL spread increases over time."""
    idx    = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [base] * n
    spreads = [0.5 + i * 0.1 for i in range(n)]
    return pd.DataFrame(
        {
            "Open":   closes,
            "High":   [c + s for c, s in zip(closes, spreads)],
            "Low":    [c - s for c, s in zip(closes, spreads)],
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
# TestComputeCVSeries
# ---------------------------------------------------------------------------

class TestComputeCVSeries:
    def test_returns_series(self):
        df = _make_ohlcv_df(200)
        cv = _compute_cv_series(df["High"], df["Low"])
        assert isinstance(cv, pd.Series)

    def test_length_matches_input(self):
        df = _make_ohlcv_df(200)
        cv = _compute_cv_series(df["High"], df["Low"])
        assert len(cv) == 200

    def test_no_nan_at_end(self):
        df = _make_ohlcv_df(200)
        cv = _compute_cv_series(df["High"], df["Low"])
        assert cv.iloc[-1] == cv.iloc[-1]  # not NaN

    def test_expanding_spread_positive_cv(self):
        """Expanding HL range → EMA_HL rising → CV > 0."""
        df = _make_expanding_hl_df(200)
        cv = _compute_cv_series(df["High"], df["Low"])
        assert float(cv.iloc[-1]) > 0.0

    def test_constant_spread_near_zero_cv(self):
        """Constant HL spread → EMA_HL constant → CV ≈ 0."""
        df = _make_ohlcv_df(200, hl_spread=2.0)  # constant spread
        cv = _compute_cv_series(df["High"], df["Low"])
        assert abs(float(cv.iloc[-1])) < 0.5

    def test_no_inf_values(self):
        import math
        df = _make_ohlcv_df(200)
        cv = _compute_cv_series(df["High"], df["Low"])
        assert all(math.isfinite(v) for v in cv.dropna())

    def test_custom_periods(self):
        df = _make_ohlcv_df(200)
        cv5 = _compute_cv_series(df["High"], df["Low"], ema_period=5, roc_period=5)
        cv20 = _compute_cv_series(df["High"], df["Low"], ema_period=20, roc_period=20)
        assert len(cv5) == len(cv20) == 200


# ---------------------------------------------------------------------------
# TestComputeCVScore
# ---------------------------------------------------------------------------

class TestComputeCVScore:
    def _make_series(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_contracting_and_above_sma_scores_high(self):
        ms = self._make_series([0.01] * 100)
        score = _compute_cv_score(-5.0, 110.0, 100.0, ms)
        assert score >= 70.0

    def test_expanding_and_below_sma_scores_low(self):
        ms = self._make_series([-0.01] * 100)
        score = _compute_cv_score(10.0, 90.0, 100.0, ms)
        assert score < 40.0

    def test_score_in_range(self):
        ms = self._make_series([0.0] * 100)
        for cv, cl, sm in [(5.0, 110.0, 100.0), (-5.0, 90.0, 100.0)]:
            score = _compute_cv_score(cv, cl, sm, ms)
            assert 0.0 <= score <= 100.0

    def test_short_series_fallback(self):
        ms = self._make_series([0.01, 0.02])
        score = _compute_cv_score(2.0, 105.0, 100.0, ms)
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
# TestComputeCVIntegration
# ---------------------------------------------------------------------------

class TestComputeCVIntegration:
    @patch("quantpilot_stock.chaikin_vol.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cv("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.chaikin_vol.engine.yf.Ticker")
    def test_fields_populated(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cv("AAPL")
        assert result.cv_value is not None
        assert isinstance(result.vol_expanding, bool)
        assert isinstance(result.price_above_sma, bool)

    @patch("quantpilot_stock.chaikin_vol.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cv("AAPL")
        assert 0.0 <= result.cv_score <= 100.0

    @patch("quantpilot_stock.chaikin_vol.engine.yf.Ticker")
    def test_rising_stock_price_above_sma(self, mock_yf):
        df = _make_ohlcv_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cv("AAPL")
        assert result.price_above_sma is True

    @patch("quantpilot_stock.chaikin_vol.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cv("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}

    @patch("quantpilot_stock.chaikin_vol.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cv("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.chaikin_vol.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cv("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.chaikin_vol.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_cv("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"


# ---------------------------------------------------------------------------
# TestChaikinVolAPI
# ---------------------------------------------------------------------------

class TestChaikinVolAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/chaikin_vol")
        assert resp.status_code == 422

    @patch("quantpilot_stock.chaikin_vol.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/chaikin_vol?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.chaikin_vol.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/chaikin_vol?ticker=AAPL").json()
        for f in ["ticker", "cv_value", "vol_expanding", "price_above_sma",
                  "cv_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.chaikin_vol.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/chaikin_vol?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
