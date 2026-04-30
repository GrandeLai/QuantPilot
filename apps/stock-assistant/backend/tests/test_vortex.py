"""Tests for Vortex Indicator — Phase F.63.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.vortex.engine import (
    _classify_signal,
    _compute_vortex_score,
    _compute_vortex_series,
    compute_vortex,
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
# TestComputeVortexSeries
# ---------------------------------------------------------------------------

class TestComputeVortexSeries:
    def test_returns_three_series(self):
        df = _make_ohlcv_df(200)
        result = _compute_vortex_series(df["High"], df["Low"], df["Close"])
        assert len(result) == 3

    def test_lengths_match_input(self):
        df = _make_ohlcv_df(200)
        vip, vim, spread = _compute_vortex_series(df["High"], df["Low"], df["Close"])
        assert len(vip) == len(vim) == len(spread) == 200

    def test_vi_values_positive(self):
        """Both VI values should be positive (ratios of absolute movements)."""
        df = _make_ohlcv_df(200)
        vip, vim, _ = _compute_vortex_series(df["High"], df["Low"], df["Close"])
        assert float(vip.iloc[-1]) > 0.0
        assert float(vim.iloc[-1]) > 0.0

    def test_rising_stock_positive_spread(self):
        """Rising stock: +VI > -VI → positive spread."""
        df = _make_ohlcv_df(200, step=2.0)
        _, _, spread = _compute_vortex_series(df["High"], df["Low"], df["Close"])
        assert float(spread.iloc[-1]) > 0.0

    def test_declining_stock_negative_spread(self):
        """Declining stock: -VI > +VI → negative spread."""
        df = _make_declining_df(200, step=2.0)
        _, _, spread = _compute_vortex_series(df["High"], df["Low"], df["Close"])
        assert float(spread.iloc[-1]) < 0.0

    def test_no_inf_values(self):
        import math
        df = _make_ohlcv_df(200)
        vip, vim, spread = _compute_vortex_series(df["High"], df["Low"], df["Close"])
        for s in (vip, vim, spread):
            assert all(math.isfinite(v) for v in s.values)


# ---------------------------------------------------------------------------
# TestComputeVortexScore
# ---------------------------------------------------------------------------

class TestComputeVortexScore:
    def _make_series(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_highest_spread_high_score(self):
        series = self._make_series([float(i) for i in range(1, 101)])
        assert _compute_vortex_score(100.0, series) > 90.0

    def test_lowest_spread_low_score(self):
        series = self._make_series([float(i) for i in range(1, 101)])
        assert _compute_vortex_score(-10.0, series) < 10.0

    def test_score_in_range(self):
        series = self._make_series([float(i) for i in range(100)])
        assert 0.0 <= _compute_vortex_score(50.0, series) <= 100.0

    def test_short_series_fallback(self):
        series = self._make_series([1.0, 2.0, 3.0])
        assert _compute_vortex_score(2.0, series) == 50.0


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
# TestComputeVortexIntegration
# ---------------------------------------------------------------------------

class TestComputeVortexIntegration:
    @patch("quantpilot_stock.vortex.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_vortex("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.vortex.engine.yf.Ticker")
    def test_components_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_vortex("AAPL")
        assert result.vi_plus is not None
        assert result.vi_minus is not None
        assert result.vi_spread is not None

    @patch("quantpilot_stock.vortex.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_vortex("AAPL")
        assert 0.0 <= result.vortex_score <= 100.0

    @patch("quantpilot_stock.vortex.engine.yf.Ticker")
    def test_rising_stock_vi_bullish(self, mock_yf):
        df = _make_ohlcv_df(300, step=2.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_vortex("AAPL")
        assert result.vi_bullish is True

    @patch("quantpilot_stock.vortex.engine.yf.Ticker")
    def test_declining_stock_vi_bearish(self, mock_yf):
        df = _make_declining_df(300, step=2.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_vortex("AAPL")
        assert result.vi_bullish is False

    @patch("quantpilot_stock.vortex.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_vortex("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.vortex.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(5)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_vortex("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.vortex.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_vortex("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.vortex.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_vortex("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}


# ---------------------------------------------------------------------------
# TestVortexAPI
# ---------------------------------------------------------------------------

class TestVortexAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/vortex")
        assert resp.status_code == 422

    @patch("quantpilot_stock.vortex.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/vortex?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.vortex.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/vortex?ticker=AAPL").json()
        for f in ["ticker", "vi_plus", "vi_minus", "vi_spread",
                  "vi_bullish", "vortex_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.vortex.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/vortex?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
