"""Tests for On-Balance Volume — Phase F.41.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.obv.engine import (
    _classify_signal,
    _compute_obv_score,
    _compute_obv_series,
    _price_obv_trend,
    compute_obv,
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
# TestComputeOBVSeries
# ---------------------------------------------------------------------------

class TestComputeOBVSeries:
    def test_rising_stock_positive_obv(self):
        df = _make_ohlcv_df(100)
        obv = _compute_obv_series(df["Close"], df["Volume"])
        # Consistently rising close → OBV should be positive and growing
        assert float(obv.iloc[-1]) > float(obv.iloc[0])

    def test_declining_stock_negative_obv(self):
        df = _make_declining_ohlcv(100)
        obv = _compute_obv_series(df["Close"], df["Volume"])
        assert float(obv.iloc[-1]) < float(obv.iloc[0])

    def test_obv_length_matches_input(self):
        df = _make_ohlcv_df(100)
        obv = _compute_obv_series(df["Close"], df["Volume"])
        assert len(obv) == len(df)

    def test_flat_price_stable_obv(self):
        """Flat price → all diffs after row 1 are 0 → OBV constant after row 1."""
        idx = pd.date_range("2022-01-01", periods=50, freq="B")
        close = pd.Series([100.0] * 50, index=idx)
        volume = pd.Series([1_000_000] * 50, index=idx)
        obv = _compute_obv_series(close, volume)
        # After the first delta (NaN → treated as no-change), remaining are 0
        # So OBV should be constant from index 2 onwards
        assert float(obv.iloc[-1]) == float(obv.iloc[2])


# ---------------------------------------------------------------------------
# TestPriceOBVTrend
# ---------------------------------------------------------------------------

class TestPriceOBVTrend:
    def test_confirming_bull(self):
        assert _price_obv_trend(0.05, 0.08) == "confirming_bull"

    def test_confirming_bear(self):
        assert _price_obv_trend(-0.05, -0.08) == "confirming_bear"

    def test_diverging_bull(self):
        assert _price_obv_trend(-0.03, 0.06) == "diverging_bull"

    def test_diverging_bear(self):
        assert _price_obv_trend(0.04, -0.07) == "diverging_bear"

    def test_none_returns_neutral(self):
        assert _price_obv_trend(None, 0.05) == "neutral"
        assert _price_obv_trend(0.05, None) == "neutral"


# ---------------------------------------------------------------------------
# TestComputeOBVScore
# ---------------------------------------------------------------------------

class TestComputeOBVScore:
    def test_bull_above_ema_positive_momentum_score_high(self):
        score = _compute_obv_score(True, 0.05, "confirming_bull")
        assert score >= 75.0

    def test_bear_below_ema_negative_momentum_score_low(self):
        score = _compute_obv_score(False, -0.05, "confirming_bear")
        assert score <= 25.0

    def test_score_in_range(self):
        for obv_above in [True, False]:
            for chg in [0.1, -0.1, None]:
                for trend in ["confirming_bull", "neutral", "confirming_bear"]:
                    score = _compute_obv_score(obv_above, chg, trend)
                    assert 0.0 <= score <= 100.0

    def test_above_ema_higher_than_below(self):
        s_above = _compute_obv_score(True, None, "neutral")
        s_below = _compute_obv_score(False, None, "neutral")
        assert s_above > s_below


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
# TestComputeOBVIntegration
# ---------------------------------------------------------------------------

class TestComputeOBVIntegration:
    @patch("quantpilot_stock.obv.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_obv("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.obv.engine.yf.Ticker")
    def test_obv_and_ema_populated(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_obv("AAPL")
        assert result.obv is not None
        assert result.obv_ema20 is not None

    @patch("quantpilot_stock.obv.engine.yf.Ticker")
    def test_rising_stock_bull_score(self, mock_yf):
        df = _make_ohlcv_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_obv("AAPL")
        assert result.obv_score > 50.0

    @patch("quantpilot_stock.obv.engine.yf.Ticker")
    def test_declining_stock_bear_score(self, mock_yf):
        df = _make_declining_ohlcv(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_obv("AAPL")
        assert result.obv_score < 50.0

    @patch("quantpilot_stock.obv.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_obv("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.obv.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(15)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_obv("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.obv.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_obv("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.obv.engine.yf.Ticker")
    def test_score_bounds(self, mock_yf):
        for df in [_make_ohlcv_df(200, step=3.0), _make_declining_ohlcv(200, step=3.0)]:
            mock_yf.return_value = _mock_ticker(df)
            result = compute_obv("AAPL")
            assert 0.0 <= result.obv_score <= 100.0

    @patch("quantpilot_stock.obv.engine.yf.Ticker")
    def test_price_obv_trend_set(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_obv("AAPL")
        assert result.price_obv_trend in (
            "confirming_bull", "confirming_bear",
            "diverging_bull", "diverging_bear", "neutral"
        )


# ---------------------------------------------------------------------------
# TestOBVAPI
# ---------------------------------------------------------------------------

class TestOBVAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/obv")
        assert resp.status_code == 422

    @patch("quantpilot_stock.obv.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/obv?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.obv.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/obv?ticker=AAPL").json()
        for f in ["ticker", "obv", "obv_ema20", "obv_above_ema",
                  "price_obv_trend", "obv_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.obv.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/obv?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
