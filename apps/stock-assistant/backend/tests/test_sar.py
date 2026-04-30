"""Tests for Parabolic SAR — Phase F.48.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.sar.engine import (
    _classify_signal,
    _compute_sar_score,
    _compute_sar_series,
    _count_trend_bars,
    compute_sar,
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
    return pd.DataFrame(
        {
            "Open": closes,
            "High": [c + 1.0 for c in closes],
            "Low": [c - 1.0 for c in closes],
            "Close": closes,
            "Volume": [volume] * n,
        },
        index=idx,
    )


def _make_declining_df(
    n: int,
    start: float = 200.0,
    step: float = 0.3,
) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [start - i * step for i in range(n)]
    return pd.DataFrame(
        {
            "Open": closes,
            "High": [c + 1.0 for c in closes],
            "Low": [c - 1.0 for c in closes],
            "Close": closes,
            "Volume": [1_000_000] * n,
        },
        index=idx,
    )


def _mock_ticker(df: pd.DataFrame) -> MagicMock:
    tk = MagicMock()
    tk.history.return_value = df
    return tk


# ---------------------------------------------------------------------------
# TestComputeSARSeries
# ---------------------------------------------------------------------------


class TestComputeSARSeries:
    def test_output_length_matches_input(self):
        df = _make_ohlcv_df(100)
        sar, bull = _compute_sar_series(df["High"], df["Low"], df["Close"])
        assert len(sar) == 100
        assert len(bull) == 100

    def test_rising_stock_sar_bullish(self):
        """For a strongly rising stock, SAR should end up below price (bullish)."""
        df = _make_ohlcv_df(100, step=2.0)
        sar, bull = _compute_sar_series(df["High"], df["Low"], df["Close"])
        assert bool(bull.iloc[-1]) is True

    def test_declining_stock_sar_bearish(self):
        """For a strongly declining stock, SAR should end up above price (bearish)."""
        df = _make_declining_df(100, step=2.0)
        sar, bull = _compute_sar_series(df["High"], df["Low"], df["Close"])
        assert bool(bull.iloc[-1]) is False

    def test_sar_above_price_in_downtrend(self):
        df = _make_declining_df(100, step=2.0)
        sar, bull = _compute_sar_series(df["High"], df["Low"], df["Close"])
        # In downtrend SAR should be above close for most tail bars
        last_close = float(df["Close"].iloc[-1])
        last_sar = float(sar.iloc[-1])
        assert last_sar > last_close

    def test_sar_below_price_in_uptrend(self):
        df = _make_ohlcv_df(100, step=2.0)
        sar, bull = _compute_sar_series(df["High"], df["Low"], df["Close"])
        last_close = float(df["Close"].iloc[-1])
        last_sar = float(sar.iloc[-1])
        assert last_sar < last_close

    def test_short_series_returns_without_crash(self):
        df = _make_ohlcv_df(3)
        sar, bull = _compute_sar_series(df["High"], df["Low"], df["Close"])
        assert len(sar) == 3

    def test_single_bar_returns_without_crash(self):
        df = _make_ohlcv_df(1)
        sar, bull = _compute_sar_series(df["High"], df["Low"], df["Close"])
        assert len(sar) == 1


# ---------------------------------------------------------------------------
# TestCountTrendBars
# ---------------------------------------------------------------------------


class TestCountTrendBars:
    def test_all_bullish_returns_positive(self):
        idx = pd.date_range("2022-01-01", periods=5, freq="B")
        bull = pd.Series([True, True, True, True, True], index=idx)
        assert _count_trend_bars(bull) == 5

    def test_all_bearish_returns_negative(self):
        idx = pd.date_range("2022-01-01", periods=5, freq="B")
        bull = pd.Series([False, False, False, False, False], index=idx)
        assert _count_trend_bars(bull) == -5

    def test_mixed_counts_only_tail_run(self):
        idx = pd.date_range("2022-01-01", periods=7, freq="B")
        bull = pd.Series([True, True, False, False, False, False, False], index=idx)
        assert _count_trend_bars(bull) == -5

    def test_empty_returns_zero(self):
        bull = pd.Series([], dtype=bool)
        assert _count_trend_bars(bull) == 0


# ---------------------------------------------------------------------------
# TestComputeSARScore
# ---------------------------------------------------------------------------


class TestComputeSARScore:
    def test_high_dist_gives_high_score(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        dist = pd.Series([0.0] * 99 + [10.0], index=idx)
        score = _compute_sar_score(10.0, dist)
        assert score > 90.0

    def test_negative_dist_gives_low_score(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        dist = pd.Series([0.0] * 99 + [-10.0], index=idx)
        score = _compute_sar_score(-10.0, dist)
        assert score < 10.0

    def test_score_in_range(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        dist = pd.Series(range(100), dtype=float, index=idx)
        score = _compute_sar_score(50.0, dist)
        assert 0.0 <= score <= 100.0

    def test_short_series_fallback(self):
        idx = pd.date_range("2022-01-01", periods=5, freq="B")
        dist = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=idx)
        score = _compute_sar_score(0.0, dist)
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
# TestComputeSARIntegration
# ---------------------------------------------------------------------------


class TestComputeSARIntegration:
    @patch("quantpilot_stock.sar.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_sar("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.sar.engine.yf.Ticker")
    def test_sar_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_sar("AAPL")
        assert result.sar is not None

    @patch("quantpilot_stock.sar.engine.yf.Ticker")
    def test_rising_stock_sar_bullish(self, mock_yf):
        df = _make_ohlcv_df(300, step=2.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_sar("AAPL")
        assert result.sar_bullish is True
        assert result.sar_direction == "up"

    @patch("quantpilot_stock.sar.engine.yf.Ticker")
    def test_declining_stock_sar_bearish(self, mock_yf):
        df = _make_declining_df(300, step=2.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_sar("AAPL")
        assert result.sar_bullish is False
        assert result.sar_direction == "down"

    @patch("quantpilot_stock.sar.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_sar("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.sar.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_sar("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.sar.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_sar("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.sar.engine.yf.Ticker")
    def test_score_bounds(self, mock_yf):
        for df in [_make_ohlcv_df(300, step=2.0), _make_declining_df(300, step=2.0)]:
            mock_yf.return_value = _mock_ticker(df)
            result = compute_sar("AAPL")
            assert 0.0 <= result.sar_score <= 100.0

    @patch("quantpilot_stock.sar.engine.yf.Ticker")
    def test_direction_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_sar("AAPL")
        assert result.sar_direction in ("up", "down")

    @patch("quantpilot_stock.sar.engine.yf.Ticker")
    def test_trend_bars_nonzero_for_strong_trend(self, mock_yf):
        df = _make_ohlcv_df(300, step=2.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_sar("AAPL")
        assert result.trend_bars != 0

    @patch("quantpilot_stock.sar.engine.yf.Ticker")
    def test_distance_pct_positive_in_uptrend(self, mock_yf):
        df = _make_ohlcv_df(300, step=2.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_sar("AAPL")
        assert result.sar_distance_pct is not None
        assert result.sar_distance_pct > 0.0

    @patch("quantpilot_stock.sar.engine.yf.Ticker")
    def test_distance_pct_negative_in_downtrend(self, mock_yf):
        # Use step=0.3 so closes stay positive (200 - 299×0.3 ≈ 110 > 0).
        # Negative closes flip the sign of the distance formula.
        df = _make_declining_df(300, step=0.3)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_sar("AAPL")
        assert result.sar_distance_pct is not None
        assert result.sar_distance_pct < 0.0


# ---------------------------------------------------------------------------
# TestSARAPI
# ---------------------------------------------------------------------------


class TestSARAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient

        from quantpilot_stock.main import create_app

        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/sar")
        assert resp.status_code == 422

    @patch("quantpilot_stock.sar.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/sar?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.sar.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/sar?ticker=AAPL").json()
        for f in ["ticker", "sar", "sar_bullish", "sar_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.sar.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/sar?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
