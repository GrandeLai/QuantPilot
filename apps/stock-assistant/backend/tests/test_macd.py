"""Tests for MACD Signal — Phase F.37.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.macd.engine import (
    _classify_signal,
    _compute_macd_score,
    _compute_macd_series,
    compute_macd,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_price_df(n: int, start: float = 100.0, step: float = 0.5) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    prices = [start + i * step for i in range(n)]
    return pd.DataFrame({"Close": prices}, index=idx)


def _make_flat_df(n: int, price: float = 100.0) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    return pd.DataFrame({"Close": [price] * n}, index=idx)


def _make_declining_df(n: int, start: float = 150.0, step: float = 0.5) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    prices = [start - i * step for i in range(n)]
    return pd.DataFrame({"Close": prices}, index=idx)


def _mock_ticker(df: pd.DataFrame) -> MagicMock:
    tk = MagicMock()
    tk.history.return_value = df
    return tk


# ---------------------------------------------------------------------------
# TestComputeMACDSeries
# ---------------------------------------------------------------------------

class TestComputeMACDSeries:
    def test_returns_three_series(self):
        df = _make_price_df(100)
        close = df["Close"]
        macd_line, sig_line, hist = _compute_macd_series(close)
        assert len(macd_line) == len(close)
        assert len(sig_line) == len(close)
        assert len(hist) == len(close)

    def test_histogram_equals_macd_minus_signal(self):
        df = _make_price_df(100)
        close = df["Close"]
        macd_line, sig_line, hist = _compute_macd_series(close)
        for i in range(len(hist)):
            assert abs(hist.iloc[i] - (macd_line.iloc[i] - sig_line.iloc[i])) < 1e-9

    def test_rising_stock_macd_positive_eventually(self):
        df = _make_price_df(200, step=1.0)
        close = df["Close"]
        macd_line, _, _ = _compute_macd_series(close)
        assert macd_line.iloc[-1] > 0

    def test_declining_stock_macd_negative_eventually(self):
        df = _make_declining_df(200)
        close = df["Close"]
        macd_line, _, _ = _compute_macd_series(close)
        assert macd_line.iloc[-1] < 0

    def test_flat_stock_macd_near_zero(self):
        df = _make_flat_df(200)
        close = df["Close"]
        macd_line, _, _ = _compute_macd_series(close)
        assert abs(macd_line.iloc[-1]) < 1e-6


# ---------------------------------------------------------------------------
# TestComputeMACDScore
# ---------------------------------------------------------------------------

class TestComputeMACDScore:
    def test_all_bullish_conditions_near_100(self):
        score = _compute_macd_score(
            macd=2.0, signal_line=1.5, histogram=0.5,
            prev_histogram=0.3,
            recent_crossover=True, crossover_direction="bull",
        )
        assert score >= 80.0

    def test_all_bearish_conditions_near_0(self):
        score = _compute_macd_score(
            macd=-2.0, signal_line=-1.5, histogram=-0.5,
            prev_histogram=-0.3,
            recent_crossover=True, crossover_direction="bear",
        )
        assert score <= 20.0

    def test_score_in_range(self):
        for macd, hist in [(1.0, 0.5), (-1.0, -0.3), (0.0, 0.0)]:
            score = _compute_macd_score(macd, macd - hist, hist, hist * 0.5, False, "")
            assert 0.0 <= score <= 100.0

    def test_no_crossover_bonus(self):
        score_no_cross = _compute_macd_score(2.0, 1.5, 0.5, 0.3, False, "")
        score_with_cross = _compute_macd_score(2.0, 1.5, 0.5, 0.3, True, "bull")
        assert score_with_cross > score_no_cross

    def test_bear_cross_lowers_score(self):
        score_no_cross = _compute_macd_score(-1.0, -0.5, -0.5, -0.3, False, "")
        score_bear_cross = _compute_macd_score(-1.0, -0.5, -0.5, -0.3, True, "bear")
        assert score_bear_cross < score_no_cross

    def test_expanding_histogram_bull_adds_score(self):
        score_flat = _compute_macd_score(1.0, 0.5, 0.5, 0.5, False, "")  # |0.5| == |0.5|, not expanding
        score_expanding = _compute_macd_score(1.0, 0.5, 0.5, 0.3, False, "")  # |0.5| > |0.3|
        assert score_expanding >= score_flat


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

    def test_boundary_80_is_strong_bull(self):
        assert _classify_signal(80.0) == "strong_bull"

    def test_boundary_60_is_bull(self):
        assert _classify_signal(60.0) == "bull"

    def test_boundary_40_is_neutral(self):
        assert _classify_signal(40.0) == "neutral"

    def test_boundary_20_is_bear(self):
        assert _classify_signal(20.0) == "bear"

    def test_boundary_19_is_strong_bear(self):
        assert _classify_signal(19.9) == "strong_bear"


# ---------------------------------------------------------------------------
# TestComputeMACDIntegration
# ---------------------------------------------------------------------------

class TestComputeMACDIntegration:
    @patch("quantpilot_stock.macd.engine.yf.Ticker")
    def test_data_available_with_adequate_data(self, mock_yf):
        df = _make_price_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_macd("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.macd.engine.yf.Ticker")
    def test_all_fields_populated(self, mock_yf):
        df = _make_price_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_macd("AAPL")
        assert result.macd is not None
        assert result.signal_line is not None
        assert result.histogram is not None

    @patch("quantpilot_stock.macd.engine.yf.Ticker")
    def test_rising_stock_bull_signal(self, mock_yf):
        df = _make_price_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_macd("AAPL")
        assert result.macd_score > 50.0

    @patch("quantpilot_stock.macd.engine.yf.Ticker")
    def test_declining_stock_bear_signal(self, mock_yf):
        df = _make_declining_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_macd("AAPL")
        assert result.macd_score < 50.0

    @patch("quantpilot_stock.macd.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_price_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_macd("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.macd.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_price_df(20)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_macd("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.macd.engine.yf.Ticker")
    def test_yfinance_exception_data_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_macd("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.macd.engine.yf.Ticker")
    def test_histogram_expanding_detected(self, mock_yf):
        df = _make_price_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_macd("AAPL")
        # Just verify the field exists
        assert isinstance(result.histogram_expanding, bool)

    @patch("quantpilot_stock.macd.engine.yf.Ticker")
    def test_score_bounds(self, mock_yf):
        for df in [_make_price_df(200, step=2.0), _make_declining_df(200, step=2.0)]:
            mock_yf.return_value = _mock_ticker(df)
            result = compute_macd("AAPL")
            assert 0.0 <= result.macd_score <= 100.0


# ---------------------------------------------------------------------------
# TestMACDAPI
# ---------------------------------------------------------------------------

class TestMACDAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/macd")
        assert resp.status_code == 422

    @patch("quantpilot_stock.macd.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_price_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/macd?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.macd.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_price_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/macd?ticker=AAPL").json()
        for f in ["ticker", "macd", "signal_line", "histogram",
                  "macd_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.macd.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/macd?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False

    @patch("quantpilot_stock.macd.engine.yf.Ticker")
    def test_crossover_direction_field(self, mock_yf):
        df = _make_price_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/macd?ticker=AAPL").json()
        assert "crossover_direction" in body
        assert body["crossover_direction"] in ("bull", "bear", "")
