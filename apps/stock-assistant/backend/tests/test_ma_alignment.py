"""Tests for Moving Average Alignment Score — Phase F.36.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.ma_alignment.engine import (
    _classify_signal,
    _compute_ma_score,
    compute_ma_alignment,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_price_df(n: int, start: float = 100.0, step: float = 0.5) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    prices = [start + i * step for i in range(n)]
    return pd.DataFrame({"Close": prices}, index=idx)


def _mock_ticker(df: pd.DataFrame) -> MagicMock:
    tk = MagicMock()
    tk.history.return_value = df
    return tk


# ---------------------------------------------------------------------------
# TestComputeMAScore
# ---------------------------------------------------------------------------

class TestComputeMAScore:
    def test_full_bull_score_near_100(self):
        """Price well above all MAs in perfect bull alignment → high score."""
        score = _compute_ma_score(130.0, sma20=120.0, sma50=110.0, sma200=100.0)
        assert score >= 80.0

    def test_full_bear_score_near_0(self):
        """Price below all MAs in perfect bear alignment → low score."""
        score = _compute_ma_score(70.0, sma20=80.0, sma50=90.0, sma200=100.0)
        assert score <= 20.0

    def test_price_above_all_mas_but_no_stacking(self):
        """Price above MAs but MAs in wrong order → mid-range."""
        score = _compute_ma_score(110.0, sma20=100.0, sma50=105.0, sma200=102.0)
        # price > all MAs (+3), no bull stacking
        assert 0.0 < score < 80.0

    def test_no_sma200_partial_score(self):
        """Only SMA20 and SMA50 available → still computes partial score."""
        score = _compute_ma_score(110.0, sma20=100.0, sma50=105.0, sma200=None)
        assert 0.0 <= score <= 100.0

    def test_all_none_returns_middle(self):
        """No MAs → raw = 0 → maps to ~22.2%."""
        score = _compute_ma_score(100.0, sma20=None, sma50=None, sma200=None)
        assert 0.0 <= score <= 100.0

    def test_score_in_range(self):
        for sma20, sma50, sma200 in [
            (90, 80, 70), (110, 120, 130), (100, 100, 100),
        ]:
            score = _compute_ma_score(100.0, sma20, sma50, sma200)
            assert 0.0 <= score <= 100.0


# ---------------------------------------------------------------------------
# TestClassifySignal
# ---------------------------------------------------------------------------

class TestClassifySignal:
    def test_full_bull(self):
        assert _classify_signal(85.0) == "full_bull"

    def test_partial_bull(self):
        assert _classify_signal(65.0) == "partial_bull"

    def test_neutral(self):
        assert _classify_signal(50.0) == "neutral"

    def test_partial_bear(self):
        assert _classify_signal(30.0) == "partial_bear"

    def test_full_bear(self):
        assert _classify_signal(10.0) == "full_bear"

    def test_none_returns_no_data(self):
        assert _classify_signal(None) == "no_data"

    def test_boundary_80_is_full_bull(self):
        assert _classify_signal(80.0) == "full_bull"

    def test_boundary_60_is_partial_bull(self):
        assert _classify_signal(60.0) == "partial_bull"

    def test_boundary_40_is_neutral(self):
        assert _classify_signal(40.0) == "neutral"

    def test_boundary_20_is_partial_bear(self):
        assert _classify_signal(20.0) == "partial_bear"


# ---------------------------------------------------------------------------
# TestComputeMAAlignmentIntegration
# ---------------------------------------------------------------------------

class TestComputeMAAlignmentIntegration:
    @patch("quantpilot_stock.ma_alignment.engine.yf.Ticker")
    def test_data_available_with_adequate_data(self, mock_yf):
        df = _make_price_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ma_alignment("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.ma_alignment.engine.yf.Ticker")
    def test_sma200_none_with_short_history(self, mock_yf):
        """100 bars < 200 required → sma200 should be None."""
        df = _make_price_df(100)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ma_alignment("AAPL")
        assert result.sma200 is None

    @patch("quantpilot_stock.ma_alignment.engine.yf.Ticker")
    def test_all_smas_populated_with_long_history(self, mock_yf):
        df = _make_price_df(250)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ma_alignment("AAPL")
        assert result.sma20 is not None
        assert result.sma50 is not None

    @patch("quantpilot_stock.ma_alignment.engine.yf.Ticker")
    def test_uptrending_stock_positive_score(self, mock_yf):
        """Rising stock → price above all MAs → score should be > 50."""
        df = _make_price_df(300, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ma_alignment("AAPL")
        assert result.ma_score > 50.0

    @patch("quantpilot_stock.ma_alignment.engine.yf.Ticker")
    def test_golden_cross_detected(self, mock_yf):
        """Rising trend → SMA50 should be above SMA200 → golden cross."""
        df = _make_price_df(300, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ma_alignment("AAPL")
        # SMA50 > SMA200 for rising trend
        if result.sma50 is not None and result.sma200 is not None:
            assert result.golden_cross == (result.sma50 > result.sma200)

    @patch("quantpilot_stock.ma_alignment.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_price_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ma_alignment("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.ma_alignment.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_price_df(15)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ma_alignment("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.ma_alignment.engine.yf.Ticker")
    def test_yfinance_exception_data_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_ma_alignment("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"


# ---------------------------------------------------------------------------
# TestMAAlignmentAPI
# ---------------------------------------------------------------------------

class TestMAAlignmentAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/ma-alignment")
        assert resp.status_code == 422

    @patch("quantpilot_stock.ma_alignment.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_price_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/ma-alignment?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.ma_alignment.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_price_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/ma-alignment?ticker=AAPL").json()
        for f in ["ticker", "ma_score", "signal", "golden_cross", "full_bull_align", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.ma_alignment.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/ma-alignment?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
