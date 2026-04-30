"""Tests for DPO (Detrended Price Oscillator) — Phase F.56.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

import math
from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.dpo.engine import (
    _classify_signal,
    _compute_dpo_score,
    _compute_dpo_series,
    compute_dpo,
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
# TestComputeDPOSeries
# ---------------------------------------------------------------------------


class TestComputeDPOSeries:
    def test_length_matches_input(self):
        df  = _make_ohlcv_df(200)
        dpo = _compute_dpo_series(df["Close"])
        assert len(dpo) == 200

    def test_rising_stock_positive_dpo(self):
        """For a linearly rising stock, current close > past SMA → DPO > 0."""
        df  = _make_ohlcv_df(200, step=1.0)
        dpo = _compute_dpo_series(df["Close"])
        assert float(dpo.iloc[-1]) > 0.0

    def test_declining_stock_negative_dpo(self):
        """For a declining stock, current close < past SMA → DPO < 0."""
        df  = _make_declining_df(200, step=1.0)
        dpo = _compute_dpo_series(df["Close"])
        assert float(dpo.iloc[-1]) < 0.0

    def test_finite_values(self):
        df  = _make_ohlcv_df(200)
        dpo = _compute_dpo_series(df["Close"])
        assert math.isfinite(float(dpo.iloc[-1]))

    def test_flat_stock_near_zero_dpo(self):
        """A flat stock has DPO ≈ 0 because close ≈ past SMA."""
        idx   = pd.date_range("2022-01-01", periods=200, freq="B")
        close = pd.Series([100.0] * 200, index=idx)
        dpo   = _compute_dpo_series(close)
        assert abs(float(dpo.iloc[-1])) < 0.01


# ---------------------------------------------------------------------------
# TestComputeDPOScore
# ---------------------------------------------------------------------------


class TestComputeDPOScore:
    def test_highest_dpo_gives_high_score(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        dpo = pd.Series([0.0] * 99 + [5.0], index=idx)
        assert _compute_dpo_score(5.0, dpo) > 90.0

    def test_lowest_dpo_gives_low_score(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        dpo = pd.Series([0.0] * 99 + [-5.0], index=idx)
        assert _compute_dpo_score(-5.0, dpo) < 10.0

    def test_score_in_range(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        dpo = pd.Series(range(-50, 50), dtype=float, index=idx)
        assert 0.0 <= _compute_dpo_score(0.0, dpo) <= 100.0

    def test_short_series_fallback(self):
        idx = pd.date_range("2022-01-01", periods=5, freq="B")
        dpo = pd.Series([1.0, -1.0, 0.5, -0.5, 0.2], index=idx)
        score = _compute_dpo_score(0.5, dpo)
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
# TestComputeDPOIntegration
# ---------------------------------------------------------------------------


class TestComputeDPOIntegration:
    @patch("quantpilot_stock.dpo.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_dpo("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.dpo.engine.yf.Ticker")
    def test_dpo_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_dpo("AAPL")
        assert result.dpo_value is not None

    @patch("quantpilot_stock.dpo.engine.yf.Ticker")
    def test_rising_stock_positive_dpo(self, mock_yf):
        df = _make_ohlcv_df(300, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_dpo("AAPL")
        assert result.dpo_positive is True

    @patch("quantpilot_stock.dpo.engine.yf.Ticker")
    def test_declining_stock_negative_dpo(self, mock_yf):
        df = _make_declining_df(300, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_dpo("AAPL")
        assert result.dpo_positive is False

    @patch("quantpilot_stock.dpo.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_dpo("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.dpo.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_dpo("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.dpo.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_dpo("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.dpo.engine.yf.Ticker")
    def test_score_bounds(self, mock_yf):
        for df in [_make_ohlcv_df(300, step=2.0), _make_declining_df(300)]:
            mock_yf.return_value = _mock_ticker(df)
            result = compute_dpo("AAPL")
            assert 0.0 <= result.dpo_score <= 100.0

    @patch("quantpilot_stock.dpo.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_dpo("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}


# ---------------------------------------------------------------------------
# TestDPOAPI
# ---------------------------------------------------------------------------


class TestDPOAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/dpo")
        assert resp.status_code == 422

    @patch("quantpilot_stock.dpo.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/dpo?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.dpo.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/dpo?ticker=AAPL").json()
        for f in ["ticker", "dpo_value", "dpo_positive", "dpo_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.dpo.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/dpo?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
