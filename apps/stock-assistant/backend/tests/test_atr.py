"""Tests for Average True Range (ATR) — Phase F.46.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.atr.engine import (
    _classify_signal,
    _compute_atr_score,
    _compute_atr_series,
    compute_atr,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv_df(
    n: int,
    start: float = 100.0,
    step: float = 0.5,
    volume: int = 1_000_000,
    hl_spread: float = 1.0,
) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [start + i * step for i in range(n)]
    return pd.DataFrame({
        "Open": closes,
        "High": [c + hl_spread for c in closes],
        "Low": [c - hl_spread for c in closes],
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
# TestComputeATRSeries
# ---------------------------------------------------------------------------

class TestComputeATRSeries:
    def test_atr_positive(self):
        df = _make_ohlcv_df(100)
        atr = _compute_atr_series(df["High"], df["Low"], df["Close"])
        assert float(atr.iloc[-1]) > 0.0

    def test_atr_length_matches_input(self):
        df = _make_ohlcv_df(100)
        atr = _compute_atr_series(df["High"], df["Low"], df["Close"])
        assert len(atr) == len(df)

    def test_wide_spread_higher_atr(self):
        """Wider H-L spread → higher ATR."""
        df_narrow = _make_ohlcv_df(100, hl_spread=0.5)
        df_wide = _make_ohlcv_df(100, hl_spread=5.0)
        atr_narrow = _compute_atr_series(df_narrow["High"], df_narrow["Low"], df_narrow["Close"])
        atr_wide = _compute_atr_series(df_wide["High"], df_wide["Low"], df_wide["Close"])
        assert float(atr_wide.iloc[-1]) > float(atr_narrow.iloc[-1])

    def test_constant_price_atr_equals_spread(self):
        """Flat close + constant spread → ATR ≈ spread (H-L)."""
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        high = pd.Series([102.0] * 100, index=idx)
        low = pd.Series([100.0] * 100, index=idx)
        close = pd.Series([101.0] * 100, index=idx)
        atr = _compute_atr_series(high, low, close)
        # ATR should converge to H-L range = 2.0
        assert abs(float(atr.iloc[-1]) - 2.0) < 0.1


# ---------------------------------------------------------------------------
# TestComputeATRScore
# ---------------------------------------------------------------------------

class TestComputeATRScore:
    def test_above_both_smas_high_score(self):
        score = _compute_atr_score(True, True, 0.5)
        assert score > 50.0

    def test_below_both_smas_low_score(self):
        score = _compute_atr_score(False, False, 0.5)
        assert score < 50.0

    def test_above_sma20_above_sma50_high_atr_bullish(self):
        """High ATR + uptrend → amplified bullish score."""
        score_high = _compute_atr_score(True, True, 0.9)
        score_normal = _compute_atr_score(True, True, 0.5)
        assert score_high > score_normal

    def test_compression_mild_positive_bias(self):
        """Low ATR (compression) → slight positive vs neutral."""
        score_compression = _compute_atr_score(True, False, 0.1)
        score_normal = _compute_atr_score(True, False, 0.5)
        assert score_compression >= score_normal - 1  # mild bias

    def test_score_clipped(self):
        assert _compute_atr_score(True, True, 1.0) <= 100.0
        assert _compute_atr_score(False, False, 0.0) >= 0.0

    def test_none_rank_still_returns_score(self):
        score = _compute_atr_score(True, True, None)
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
# TestComputeATRIntegration
# ---------------------------------------------------------------------------

class TestComputeATRIntegration:
    @patch("quantpilot_stock.atr.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_atr("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.atr.engine.yf.Ticker")
    def test_atr_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_atr("AAPL")
        assert result.atr is not None
        assert result.atr > 0.0

    @patch("quantpilot_stock.atr.engine.yf.Ticker")
    def test_atr_pct_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_atr("AAPL")
        assert result.atr_pct is not None

    @patch("quantpilot_stock.atr.engine.yf.Ticker")
    def test_rising_stock_above_smas(self, mock_yf):
        df = _make_ohlcv_df(300, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_atr("AAPL")
        assert result.above_sma20 is True
        assert result.above_sma50 is True

    @patch("quantpilot_stock.atr.engine.yf.Ticker")
    def test_declining_stock_below_smas(self, mock_yf):
        df = _make_declining_ohlcv(300, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_atr("AAPL")
        assert result.above_sma20 is False
        assert result.above_sma50 is False

    @patch("quantpilot_stock.atr.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_atr("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.atr.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(30)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_atr("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.atr.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_atr("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.atr.engine.yf.Ticker")
    def test_score_bounds(self, mock_yf):
        for df in [_make_ohlcv_df(300, step=2.0), _make_declining_ohlcv(300, step=2.0)]:
            mock_yf.return_value = _mock_ticker(df)
            result = compute_atr("AAPL")
            assert 0.0 <= result.atr_score <= 100.0

    @patch("quantpilot_stock.atr.engine.yf.Ticker")
    def test_volatility_regime_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_atr("AAPL")
        assert result.volatility_regime in ("high", "normal", "low")


# ---------------------------------------------------------------------------
# TestATRAPI
# ---------------------------------------------------------------------------

class TestATRAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/atr")
        assert resp.status_code == 422

    @patch("quantpilot_stock.atr.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/atr?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.atr.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/atr?ticker=AAPL").json()
        for f in ["ticker", "atr", "atr_pct", "atr_pct_rank", "volatility_regime",
                  "above_sma20", "above_sma50", "atr_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.atr.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/atr?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
