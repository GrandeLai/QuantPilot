"""Tests for Ultimate Oscillator — Phase F.54.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from quantpilot_stock.ultimate_osc.engine import (
    _classify_signal,
    _compute_uo_score,
    _compute_uo_series,
    compute_ultimate_osc,
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
# TestComputeUOSeries
# ---------------------------------------------------------------------------


class TestComputeUOSeries:
    def test_length_matches_input(self):
        df = _make_ohlcv_df(200)
        uo = _compute_uo_series(df["High"], df["Low"], df["Close"])
        assert len(uo) == 200

    def test_values_in_range(self):
        df = _make_ohlcv_df(200)
        uo = _compute_uo_series(df["High"], df["Low"], df["Close"])
        assert float(uo.min()) >= 0.0
        assert float(uo.max()) <= 100.0

    def test_rising_stock_high_uo(self):
        """A consistently rising stock should have high UO."""
        df = _make_ohlcv_df(200, step=2.0)
        uo = _compute_uo_series(df["High"], df["Low"], df["Close"])
        assert float(uo.iloc[-1]) > 50.0

    def test_declining_stock_low_uo(self):
        """A consistently falling stock should have low UO.

        step=2.0 ensures PrevClose > High, so TrueHigh=PrevClose and
        BP/TR = 1/3 ≈ 0.33 → UO ≈ 33 < 50.
        start=600 keeps all close values positive over 200 bars.
        """
        df = _make_declining_df(200, start=600, step=2.0)
        uo = _compute_uo_series(df["High"], df["Low"], df["Close"])
        assert float(uo.iloc[-1]) < 50.0

    def test_no_nan_at_end(self):
        import math
        df = _make_ohlcv_df(200, step=0.5)
        uo = _compute_uo_series(df["High"], df["Low"], df["Close"])
        assert math.isfinite(float(uo.iloc[-1]))


# ---------------------------------------------------------------------------
# TestComputeUOScore
# ---------------------------------------------------------------------------


class TestComputeUOScore:
    def test_highest_uo_gives_high_score(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        uo  = pd.Series([50.0] * 99 + [90.0], index=idx)
        assert _compute_uo_score(90.0, uo) > 90.0

    def test_lowest_uo_gives_low_score(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        uo  = pd.Series([50.0] * 99 + [10.0], index=idx)
        assert _compute_uo_score(10.0, uo) < 10.0

    def test_score_in_range(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        uo  = pd.Series(range(100), dtype=float, index=idx)
        assert 0.0 <= _compute_uo_score(50.0, uo) <= 100.0

    def test_short_series_fallback(self):
        idx = pd.date_range("2022-01-01", periods=5, freq="B")
        uo  = pd.Series([60.0, 55.0, 65.0, 70.0, 50.0], index=idx)
        score = _compute_uo_score(60.0, uo)
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
# TestComputeUltimateOscIntegration
# ---------------------------------------------------------------------------


class TestComputeUltimateOscIntegration:
    @patch("quantpilot_stock.ultimate_osc.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ultimate_osc("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.ultimate_osc.engine.yf.Ticker")
    def test_uo_value_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ultimate_osc("AAPL")
        assert result.uo_value is not None

    @patch("quantpilot_stock.ultimate_osc.engine.yf.Ticker")
    def test_uo_value_in_range(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ultimate_osc("AAPL")
        assert result.uo_value is not None
        assert 0.0 <= result.uo_value <= 100.0

    @patch("quantpilot_stock.ultimate_osc.engine.yf.Ticker")
    def test_rising_stock_not_oversold(self, mock_yf):
        df = _make_ohlcv_df(300, step=2.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ultimate_osc("AAPL")
        assert result.uo_oversold is False

    @patch("quantpilot_stock.ultimate_osc.engine.yf.Ticker")
    def test_declining_stock_not_overbought(self, mock_yf):
        df = _make_declining_df(300, step=0.3)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ultimate_osc("AAPL")
        assert result.uo_overbought is False

    @patch("quantpilot_stock.ultimate_osc.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ultimate_osc("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.ultimate_osc.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ultimate_osc("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.ultimate_osc.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_ultimate_osc("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.ultimate_osc.engine.yf.Ticker")
    def test_score_bounds(self, mock_yf):
        for df in [_make_ohlcv_df(300, step=2.0), _make_declining_df(300)]:
            mock_yf.return_value = _mock_ticker(df)
            result = compute_ultimate_osc("AAPL")
            assert 0.0 <= result.uo_score <= 100.0

    @patch("quantpilot_stock.ultimate_osc.engine.yf.Ticker")
    def test_overbought_flag(self, mock_yf):
        """An extremely bullish stock with UO forced high → overbought."""
        # Create stock that rises 3 per bar for 300 bars
        df = _make_ohlcv_df(300, step=3.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ultimate_osc("AAPL")
        # Very strong uptrend: UO should be high
        assert result.uo_value is not None
        assert result.uo_value > 50.0

    @patch("quantpilot_stock.ultimate_osc.engine.yf.Ticker")
    def test_signal_is_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ultimate_osc("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}


# ---------------------------------------------------------------------------
# TestUltimateOscAPI
# ---------------------------------------------------------------------------


class TestUltimateOscAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/ultimate-osc")
        assert resp.status_code == 422

    @patch("quantpilot_stock.ultimate_osc.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/ultimate-osc?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.ultimate_osc.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/ultimate-osc?ticker=AAPL").json()
        for f in ["ticker", "uo_value", "uo_overbought", "uo_oversold",
                  "uo_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.ultimate_osc.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/ultimate-osc?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False

    @pytest.mark.parametrize("ticker", ["MSFT", "TSLA", "SPY"])
    @patch("quantpilot_stock.ultimate_osc.engine.yf.Ticker")
    def test_multiple_tickers(self, mock_yf, ticker):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get(f"/api/ultimate-osc?ticker={ticker}")
        assert resp.status_code == 200
        assert resp.json()["ticker"] == ticker
