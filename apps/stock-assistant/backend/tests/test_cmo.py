"""Tests for Chande Momentum Oscillator (CMO) — Phase F.65.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.cmo.engine import (
    _classify_signal,
    _compute_cmo_score,
    _compute_cmo_series,
    compute_cmo,
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
# TestComputeCMOSeries
# ---------------------------------------------------------------------------

class TestComputeCMOSeries:
    def test_returns_two_series(self):
        df = _make_ohlcv_df(200)
        result = _compute_cmo_series(df["Close"])
        assert len(result) == 2

    def test_lengths_match_input(self):
        df = _make_ohlcv_df(200)
        cmo, sig = _compute_cmo_series(df["Close"])
        assert len(cmo) == len(sig) == 200

    def test_rising_stock_positive_cmo(self):
        """Steadily rising price → all up-moves, CMO near +100."""
        df = _make_ohlcv_df(200, step=1.0)
        cmo, _ = _compute_cmo_series(df["Close"])
        assert float(cmo.iloc[-1]) > 50.0

    def test_declining_stock_negative_cmo(self):
        """Steadily declining price → all down-moves, CMO near −100."""
        df = _make_declining_df(200, step=0.3)
        cmo, _ = _compute_cmo_series(df["Close"])
        assert float(cmo.iloc[-1]) < 0.0

    def test_cmo_bounded(self):
        """CMO must stay within [−100, 100]."""
        df = _make_ohlcv_df(200, step=2.0)
        cmo, _ = _compute_cmo_series(df["Close"])
        assert float(cmo.min()) >= -100.0
        assert float(cmo.max()) <= 100.0

    def test_no_inf_values(self):
        import math
        df = _make_ohlcv_df(200)
        cmo, sig = _compute_cmo_series(df["Close"])
        for s in (cmo, sig):
            assert all(math.isfinite(v) for v in s.dropna().values)

    def test_flat_price_returns_zero_cmo(self):
        """Flat price → no up or down moves → CMO = 0."""
        idx = pd.date_range("2022-01-01", periods=50, freq="B")
        closes = pd.Series([100.0] * 50, index=idx)
        cmo, _ = _compute_cmo_series(closes)
        assert float(cmo.iloc[-1]) == 0.0


# ---------------------------------------------------------------------------
# TestComputeCMOScore
# ---------------------------------------------------------------------------

class TestComputeCMOScore:
    def _make_series(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_all_bullish_high_score(self):
        """CMO above signal and positive, top of distribution → high score."""
        series = self._make_series(list(range(-50, 51)))
        score = _compute_cmo_score(80.0, 50.0, series)
        assert score >= 60.0

    def test_all_bearish_low_score(self):
        """CMO below signal and negative, bottom of distribution → low score."""
        series = self._make_series(list(range(-50, 0)))
        score = _compute_cmo_score(-30.0, 0.0, series)
        assert score < 40.0

    def test_score_in_range(self):
        series = self._make_series([float(i) for i in range(-50, 51)])
        for cmo, sig in [(50.0, 20.0), (-20.0, 10.0)]:
            score = _compute_cmo_score(cmo, sig, series)
            assert 0.0 <= score <= 100.0

    def test_short_series_fallback(self):
        series = self._make_series([1.0, 2.0, 3.0])
        score = _compute_cmo_score(10.0, 5.0, series)
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
# TestComputeCMOIntegration
# ---------------------------------------------------------------------------

class TestComputeCMOIntegration:
    @patch("quantpilot_stock.cmo.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cmo("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.cmo.engine.yf.Ticker")
    def test_fields_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cmo("AAPL")
        assert isinstance(result.cmo_above_signal, bool)
        assert isinstance(result.cmo_positive, bool)
        assert result.cmo_value is not None
        assert result.signal_value is not None

    @patch("quantpilot_stock.cmo.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cmo("AAPL")
        assert 0.0 <= result.cmo_score <= 100.0

    @patch("quantpilot_stock.cmo.engine.yf.Ticker")
    def test_cmo_value_bounded(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cmo("AAPL")
        assert result.cmo_value is not None
        assert -100.0 <= result.cmo_value <= 100.0

    @patch("quantpilot_stock.cmo.engine.yf.Ticker")
    def test_rising_stock_positive_cmo(self, mock_yf):
        df = _make_ohlcv_df(300, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cmo("AAPL")
        assert result.cmo_positive is True

    @patch("quantpilot_stock.cmo.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cmo("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.cmo.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cmo("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.cmo.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_cmo("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.cmo.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cmo("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}


# ---------------------------------------------------------------------------
# TestCMOAPI
# ---------------------------------------------------------------------------

class TestCMOAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/cmo")
        assert resp.status_code == 422

    @patch("quantpilot_stock.cmo.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/cmo?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.cmo.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/cmo?ticker=AAPL").json()
        for f in ["ticker", "cmo_value", "cmo_above_signal", "cmo_positive",
                  "cmo_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.cmo.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/cmo?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
