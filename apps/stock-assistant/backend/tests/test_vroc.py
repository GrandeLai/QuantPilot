"""Tests for Volume Rate of Change (VROC) — F.84.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.vroc.engine import (
    _classify_signal,
    _compute_vroc_score,
    _compute_vroc_series,
    compute_vroc,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv_df(
    n: int,
    start: float = 100.0,
    step: float = 0.5,
    vol_base: int = 1_000_000,
    vol_trend: int = 10_000,
) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [start + i * step for i in range(n)]
    volumes = [vol_base + i * vol_trend for i in range(n)]
    return pd.DataFrame(
        {
            "Open":   closes,
            "High":   [c + 1.0 for c in closes],
            "Low":    [c - 1.0 for c in closes],
            "Close":  closes,
            "Volume": volumes,
        },
        index=idx,
    )


def _make_declining_vol_df(n: int) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [100.0 + i * 0.5 for i in range(n)]
    volumes = [max(100_000, 2_000_000 - i * 10_000) for i in range(n)]
    return pd.DataFrame(
        {
            "Open":   closes,
            "High":   [c + 1.0 for c in closes],
            "Low":    [c - 1.0 for c in closes],
            "Close":  closes,
            "Volume": volumes,
        },
        index=idx,
    )


def _mock_ticker(df: pd.DataFrame) -> MagicMock:
    tk = MagicMock()
    tk.history.return_value = df
    return tk


def _make_vol_series(vals: list[float]) -> pd.Series:
    idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
    return pd.Series(vals, index=idx)


# ---------------------------------------------------------------------------
# TestComputeVROCSeries
# ---------------------------------------------------------------------------

class TestComputeVROCSeries:
    def test_returns_series(self):
        vol = _make_vol_series([1_000_000.0] * 50)
        vroc = _compute_vroc_series(vol)
        assert isinstance(vroc, pd.Series)

    def test_length_preserved(self):
        vol = _make_vol_series([1_000_000.0] * 50)
        vroc = _compute_vroc_series(vol)
        assert len(vroc) == 50

    def test_flat_volume_gives_zero_vroc(self):
        vol = _make_vol_series([1_000_000.0] * 50)
        vroc = _compute_vroc_series(vol, period=14)
        # After warm-up, all VROC should be 0
        assert abs(float(vroc.iloc[-1])) < 1e-6

    def test_rising_volume_gives_positive_vroc(self):
        vol = _make_vol_series([1_000_000.0 + i * 10_000 for i in range(50)])
        vroc = _compute_vroc_series(vol, period=14)
        assert float(vroc.iloc[-1]) > 0.0

    def test_declining_volume_gives_negative_vroc(self):
        vol = _make_vol_series([2_000_000.0 - i * 10_000 for i in range(50)])
        vroc = _compute_vroc_series(vol, period=14)
        assert float(vroc.iloc[-1]) < 0.0

    def test_no_nan_values(self):
        vol = _make_vol_series([1_000_000.0 + i * 1000 for i in range(100)])
        vroc = _compute_vroc_series(vol)
        assert not vroc.isna().any()

    def test_zero_prev_volume_handled(self):
        """Zero volume in past → VROC defaults to 0.0 (no NaN)."""
        vals = [0.0] * 10 + [1_000_000.0] * 40
        vol = _make_vol_series(vals)
        vroc = _compute_vroc_series(vol, period=5)
        assert not vroc.isna().any()

    def test_doubling_volume_gives_100_pct(self):
        """Volume doubling → VROC should be exactly 100%."""
        # vol[t-14] = 1M, vol[t] = 2M → VROC = 100% at index 14
        vals = [1_000_000.0] * 14 + [2_000_000.0]
        vol = _make_vol_series(vals)
        vroc = _compute_vroc_series(vol, period=14)
        assert abs(float(vroc.iloc[-1]) - 100.0) < 1e-6


# ---------------------------------------------------------------------------
# TestComputeVROCScore
# ---------------------------------------------------------------------------

class TestComputeVROCScore:
    def test_rising_positive_vroc_scores_high(self):
        vroc = _make_vol_series([10.0 + i * 0.5 for i in range(252)])
        score = _compute_vroc_score(vroc)
        assert score >= 60.0

    def test_falling_negative_vroc_scores_low(self):
        vroc = _make_vol_series([-10.0 - i * 0.5 for i in range(252)])
        score = _compute_vroc_score(vroc)
        assert score < 40.0

    def test_score_in_range(self):
        vroc = _make_vol_series([0.0] * 100)
        score = _compute_vroc_score(vroc)
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


# ---------------------------------------------------------------------------
# TestComputeVROCIntegration
# ---------------------------------------------------------------------------

class TestComputeVROCIntegration:
    @patch("quantpilot_stock.vroc.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(100)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_vroc("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.vroc.engine.yf.Ticker")
    def test_fields_populated(self, mock_yf):
        df = _make_ohlcv_df(100)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_vroc("AAPL")
        assert result.vroc_value is not None

    @patch("quantpilot_stock.vroc.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(100)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_vroc("AAPL")
        assert 0.0 <= result.vroc_score <= 100.0

    @patch("quantpilot_stock.vroc.engine.yf.Ticker")
    def test_rising_volume_positive_vroc(self, mock_yf):
        df = _make_ohlcv_df(100, vol_trend=50_000)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_vroc("AAPL")
        assert result.vroc_value is not None
        assert result.vroc_value > 0.0

    @patch("quantpilot_stock.vroc.engine.yf.Ticker")
    def test_declining_volume_negative_vroc(self, mock_yf):
        df = _make_declining_vol_df(100)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_vroc("AAPL")
        assert result.vroc_value is not None
        assert result.vroc_value < 0.0

    @patch("quantpilot_stock.vroc.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(100)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_vroc("AAPL")
        valid = {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}
        assert result.signal in valid

    @patch("quantpilot_stock.vroc.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(100)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_vroc("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.vroc.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(5)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_vroc("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.vroc.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_vroc("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"


# ---------------------------------------------------------------------------
# TestVROCAPI
# ---------------------------------------------------------------------------

class TestVROCAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/vroc")
        assert resp.status_code == 422

    @patch("quantpilot_stock.vroc.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(100)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/vroc?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.vroc.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(100)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/vroc?ticker=AAPL").json()
        for f in ["ticker", "vroc_value", "vroc_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.vroc.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/vroc?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
