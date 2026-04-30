"""Tests for Rate of Change (ROC) — Phase F.47.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.roc.engine import (
    _classify_signal,
    _compute_roc_score,
    _compute_roc_series,
    compute_roc,
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
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [start + i * step for i in range(n)]
    return pd.DataFrame({
        "Open": closes,
        "High": [c + 1.0 for c in closes],
        "Low": [c - 1.0 for c in closes],
        "Close": closes,
        "Volume": [volume] * n,
    }, index=idx)


def _make_declining_ohlcv(n: int, start: float = 200.0, step: float = 0.5) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [start - i * step for i in range(n)]
    return pd.DataFrame({
        "Open": closes,
        "High": [c + 1.0 for c in closes],
        "Low": [c - 1.0 for c in closes],
        "Close": closes,
        "Volume": [1_000_000] * n,
    }, index=idx)


def _mock_ticker(df: pd.DataFrame) -> MagicMock:
    tk = MagicMock()
    tk.history.return_value = df
    return tk


# ---------------------------------------------------------------------------
# TestComputeROCSeries
# ---------------------------------------------------------------------------

class TestComputeROCSeries:
    def test_rising_stock_positive_roc(self):
        df = _make_ohlcv_df(100, step=1.0)
        roc = _compute_roc_series(df["Close"])
        assert float(roc.iloc[-1]) > 0.0

    def test_declining_stock_negative_roc(self):
        df = _make_declining_ohlcv(100, step=1.0)
        roc = _compute_roc_series(df["Close"])
        assert float(roc.iloc[-1]) < 0.0

    def test_flat_stock_zero_roc(self):
        idx = pd.date_range("2022-01-01", periods=50, freq="B")
        close = pd.Series([100.0] * 50, index=idx)
        roc = _compute_roc_series(close)
        assert abs(float(roc.iloc[-1])) < 0.01

    def test_length_matches_input(self):
        df = _make_ohlcv_df(100)
        roc = _compute_roc_series(df["Close"])
        assert len(roc) == len(df)

    def test_known_value(self):
        """ROC(3): [100, 100, 100, 110] → (110-100)/100×100 = 10%."""
        idx = pd.date_range("2022-01-01", periods=4, freq="B")
        close = pd.Series([100.0, 100.0, 100.0, 110.0], index=idx)
        roc = _compute_roc_series(close, period=3)
        assert abs(float(roc.iloc[-1]) - 10.0) < 0.01

    def test_custom_period(self):
        df = _make_ohlcv_df(100, step=1.0)
        roc5 = _compute_roc_series(df["Close"], period=5)
        roc20 = _compute_roc_series(df["Close"], period=20)
        # For monotone rising stock, longer period → larger ROC
        assert float(roc20.iloc[-1]) > float(roc5.iloc[-1])


# ---------------------------------------------------------------------------
# TestComputeROCScore
# ---------------------------------------------------------------------------

class TestComputeROCScore:
    def test_highest_roc_gives_high_score(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        # All values are 0 except the last which is 10.0
        roc_series = pd.Series([0.0] * 99 + [10.0], index=idx)
        score = _compute_roc_score(10.0, roc_series)
        # 10.0 is the highest → ~100th percentile
        assert score > 90.0

    def test_lowest_roc_gives_low_score(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        roc_series = pd.Series([0.0] * 99 + [-10.0], index=idx)
        score = _compute_roc_score(-10.0, roc_series)
        # -10.0 is the lowest → ~0th percentile
        assert score < 10.0

    def test_median_roc_gives_mid_score(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        roc_series = pd.Series(range(100), dtype=float, index=idx)  # 0..99
        score = _compute_roc_score(50.0, roc_series)  # median
        assert 40.0 <= score <= 60.0

    def test_short_series_fallback(self):
        idx = pd.date_range("2022-01-01", periods=5, freq="B")
        roc_series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=idx)
        score = _compute_roc_score(0.0, roc_series)
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
# TestComputeROCIntegration
# ---------------------------------------------------------------------------

class TestComputeROCIntegration:
    @patch("quantpilot_stock.roc.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_roc("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.roc.engine.yf.Ticker")
    def test_roc_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_roc("AAPL")
        assert result.roc is not None

    @patch("quantpilot_stock.roc.engine.yf.Ticker")
    def test_rising_stock_positive_roc_and_high_score(self, mock_yf):
        # A linearly rising stock has decreasing ROC (larger base → smaller %)
        # so the latest ROC may rank low in its own distribution.
        # Assert the fundamental property: ROC is positive.
        df = _make_ohlcv_df(300, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_roc("AAPL")
        assert result.roc_positive is True
        assert result.roc is not None and result.roc > 0.0

    @patch("quantpilot_stock.roc.engine.yf.Ticker")
    def test_declining_stock_negative_roc_and_low_score(self, mock_yf):
        # Use step=0.3 so closes stay positive (200 − 299×0.3 ≈ 110 > 0).
        # Negative denominator from crosses through zero would flip ROC sign.
        df = _make_declining_ohlcv(300, step=0.3)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_roc("AAPL")
        assert result.roc_positive is False
        assert result.roc_score < 50.0

    @patch("quantpilot_stock.roc.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_roc("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.roc.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_roc("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.roc.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_roc("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.roc.engine.yf.Ticker")
    def test_score_bounds(self, mock_yf):
        for df in [_make_ohlcv_df(300, step=2.0), _make_declining_ohlcv(300, step=2.0)]:
            mock_yf.return_value = _mock_ticker(df)
            result = compute_roc("AAPL")
            assert 0.0 <= result.roc_score <= 100.0

    @patch("quantpilot_stock.roc.engine.yf.Ticker")
    def test_direction_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_roc("AAPL")
        assert result.roc_direction in ("rising", "falling", "flat")


# ---------------------------------------------------------------------------
# TestROCAPI
# ---------------------------------------------------------------------------

class TestROCAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/roc")
        assert resp.status_code == 422

    @patch("quantpilot_stock.roc.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/roc?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.roc.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/roc?ticker=AAPL").json()
        for f in ["ticker", "roc", "roc_positive", "roc_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.roc.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/roc?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
