"""Tests for Commodity Channel Index — Phase F.45.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.cci.engine import (
    _classify_signal,
    _compute_cci_score,
    _compute_cci_series,
    compute_cci,
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


def _make_declining_ohlcv(n: int, start: float = 150.0, step: float = 0.5) -> pd.DataFrame:
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
# TestComputeCCISeries
# ---------------------------------------------------------------------------

class TestComputeCCISeries:
    def test_rising_stock_positive_cci(self):
        """Consistently rising → TP above SMA → CCI > 0."""
        df = _make_ohlcv_df(100, step=1.0)
        cci = _compute_cci_series(df["High"], df["Low"], df["Close"])
        assert float(cci.iloc[-1]) > 0.0

    def test_declining_stock_negative_cci(self):
        """Consistently declining → TP below SMA → CCI < 0."""
        df = _make_declining_ohlcv(100, step=1.0)
        cci = _compute_cci_series(df["High"], df["Low"], df["Close"])
        assert float(cci.iloc[-1]) < 0.0

    def test_flat_price_cci_near_zero(self):
        """Flat price → TP ≈ SMA → CCI ≈ 0."""
        idx = pd.date_range("2022-01-01", periods=60, freq="B")
        df = pd.DataFrame({
            "High": [102.0] * 60,
            "Low": [100.0] * 60,
            "Close": [101.0] * 60,
            "Volume": [1_000_000] * 60,
        }, index=idx)
        cci = _compute_cci_series(df["High"], df["Low"], df["Close"])
        # With completely flat prices, CCI should be 0 (or near 0 since mad=0, filled with 0)
        assert abs(float(cci.iloc[-1])) < 1.0

    def test_length_matches_input(self):
        df = _make_ohlcv_df(100)
        cci = _compute_cci_series(df["High"], df["Low"], df["Close"])
        assert len(cci) == len(df)

    def test_overbought_rising_fast(self):
        """Very fast rising → CCI > 100."""
        df = _make_ohlcv_df(100, step=5.0)
        cci = _compute_cci_series(df["High"], df["Low"], df["Close"])
        assert float(cci.iloc[-1]) > 100.0

    def test_oversold_declining_fast(self):
        """Very fast declining → CCI < -100."""
        df = _make_declining_ohlcv(100, step=5.0)
        cci = _compute_cci_series(df["High"], df["Low"], df["Close"])
        assert float(cci.iloc[-1]) < -100.0


# ---------------------------------------------------------------------------
# TestComputeCCIScore
# ---------------------------------------------------------------------------

class TestComputeCCIScore:
    def test_cci_plus_200_score_100(self):
        assert abs(_compute_cci_score(200.0) - 100.0) < 0.01

    def test_cci_minus_200_score_0(self):
        assert abs(_compute_cci_score(-200.0) - 0.0) < 0.01

    def test_cci_zero_score_50(self):
        assert abs(_compute_cci_score(0.0) - 50.0) < 0.01

    def test_cci_positive_score_above_50(self):
        assert _compute_cci_score(100.0) > 50.0

    def test_cci_negative_score_below_50(self):
        assert _compute_cci_score(-100.0) < 50.0

    def test_score_clipped(self):
        assert _compute_cci_score(500.0) <= 100.0
        assert _compute_cci_score(-500.0) >= 0.0


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
# TestComputeCCIIntegration
# ---------------------------------------------------------------------------

class TestComputeCCIIntegration:
    @patch("quantpilot_stock.cci.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cci("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.cci.engine.yf.Ticker")
    def test_cci_populated(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cci("AAPL")
        assert result.cci is not None

    @patch("quantpilot_stock.cci.engine.yf.Ticker")
    def test_rising_stock_bull_score(self, mock_yf):
        df = _make_ohlcv_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cci("AAPL")
        assert result.cci_score > 50.0

    @patch("quantpilot_stock.cci.engine.yf.Ticker")
    def test_declining_stock_bear_score(self, mock_yf):
        df = _make_declining_ohlcv(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cci("AAPL")
        assert result.cci_score < 50.0

    @patch("quantpilot_stock.cci.engine.yf.Ticker")
    def test_overbought_flag(self, mock_yf):
        """Fast rising stock → CCI > 100 → overbought."""
        df = _make_ohlcv_df(200, step=5.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cci("AAPL")
        assert result.overbought is True

    @patch("quantpilot_stock.cci.engine.yf.Ticker")
    def test_oversold_flag(self, mock_yf):
        """Fast declining stock → CCI < -100 → oversold."""
        df = _make_declining_ohlcv(200, step=5.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cci("AAPL")
        assert result.oversold is True

    @patch("quantpilot_stock.cci.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cci("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.cci.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cci("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.cci.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_cci("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.cci.engine.yf.Ticker")
    def test_score_bounds(self, mock_yf):
        for df in [_make_ohlcv_df(200, step=3.0), _make_declining_ohlcv(200, step=3.0)]:
            mock_yf.return_value = _mock_ticker(df)
            result = compute_cci("AAPL")
            assert 0.0 <= result.cci_score <= 100.0

    @patch("quantpilot_stock.cci.engine.yf.Ticker")
    def test_direction_populated(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_cci("AAPL")
        assert result.cci_direction in ("rising", "falling", "flat")


# ---------------------------------------------------------------------------
# TestCCIAPI
# ---------------------------------------------------------------------------

class TestCCIAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/cci")
        assert resp.status_code == 422

    @patch("quantpilot_stock.cci.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/cci?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.cci.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/cci?ticker=AAPL").json()
        for f in ["ticker", "cci", "overbought", "oversold",
                  "cci_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.cci.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/cci?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
