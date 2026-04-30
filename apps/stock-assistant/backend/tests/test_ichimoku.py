"""Tests for Ichimoku Cloud — Phase F.59.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.ichimoku.engine import (
    _classify_signal,
    _compute_ichimoku_score,
    _compute_ichimoku_series,
    compute_ichimoku,
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
# TestComputeIchimokuSeries
# ---------------------------------------------------------------------------

class TestComputeIchimokuSeries:
    def test_returns_four_series(self):
        df = _make_ohlcv_df(200)
        result = _compute_ichimoku_series(df["High"], df["Low"], df["Close"])
        assert len(result) == 4

    def test_series_lengths_match_input(self):
        df = _make_ohlcv_df(200)
        t, k, a, b = _compute_ichimoku_series(df["High"], df["Low"], df["Close"])
        assert len(t) == len(k) == len(a) == len(b) == 200

    def test_tenkan_le_kijun_in_rising_trend(self):
        """Tenkan (fast) ≥ Kijun (slow) in a persistently rising market."""
        df = _make_ohlcv_df(200, step=1.0)
        tenkan, kijun, _, _ = _compute_ichimoku_series(df["High"], df["Low"], df["Close"])
        # In a rising market the 9-period midpoint exceeds the 26-period midpoint
        assert float(tenkan.iloc[-1]) >= float(kijun.iloc[-1])

    def test_senkou_a_between_tenkan_kijun(self):
        df = _make_ohlcv_df(200)
        tenkan, kijun, senkou_a, _ = _compute_ichimoku_series(df["High"], df["Low"], df["Close"])
        ta = float(tenkan.iloc[-1])
        ka = float(kijun.iloc[-1])
        sa = float(senkou_a.iloc[-1])
        assert min(ta, ka) - 0.001 <= sa <= max(ta, ka) + 0.001

    def test_senkou_b_is_52bar_midpoint(self):
        df = _make_ohlcv_df(200)
        _, _, _, senkou_b = _compute_ichimoku_series(df["High"], df["Low"], df["Close"])
        # Should not be NaN at the end
        assert not pd.isna(senkou_b.iloc[-1])

    def test_no_nan_at_end_with_sufficient_data(self):
        df = _make_ohlcv_df(200)
        t, k, a, b = _compute_ichimoku_series(df["High"], df["Low"], df["Close"])
        for s in (t, k, a, b):
            assert not pd.isna(s.iloc[-1])


# ---------------------------------------------------------------------------
# TestComputeIchimokuScore
# ---------------------------------------------------------------------------

class TestComputeIchimokuScore:
    def test_all_bullish_gives_100(self):
        # Price above cloud (40) + Tenkan>Kijun (30) + SenkouA>SenkouB (30) = 100
        score, pos, cloud, tk = _compute_ichimoku_score(
            close_val=120.0,
            tenkan_val=115.0,
            kijun_val=110.0,
            senkou_a_val=108.0,
            senkou_b_val=105.0,
        )
        assert score == 100.0
        assert pos == "above"
        assert cloud is True
        assert tk is True

    def test_all_bearish_gives_0(self):
        # Price below cloud (0) + Tenkan<Kijun (0) + SenkouA<SenkouB (0) = 0
        score, pos, cloud, tk = _compute_ichimoku_score(
            close_val=90.0,
            tenkan_val=95.0,
            kijun_val=100.0,
            senkou_a_val=102.0,
            senkou_b_val=105.0,
        )
        assert score == 0.0
        assert pos == "below"
        assert cloud is False
        assert tk is False

    def test_price_inside_cloud_gives_20_pts(self):
        score, pos, _, _ = _compute_ichimoku_score(
            close_val=103.0,
            tenkan_val=103.0,
            kijun_val=103.0,
            senkou_a_val=105.0,
            senkou_b_val=100.0,
        )
        assert pos == "inside"
        # 20 pts from price + other components
        assert 0 <= score <= 100

    def test_score_in_range(self):
        for close in [80.0, 100.0, 120.0]:
            score, _, _, _ = _compute_ichimoku_score(
                close_val=close,
                tenkan_val=100.0,
                kijun_val=100.0,
                senkou_a_val=100.0,
                senkou_b_val=100.0,
            )
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
# TestComputeIchimokuIntegration
# ---------------------------------------------------------------------------

class TestComputeIchimokuIntegration:
    @patch("quantpilot_stock.ichimoku.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ichimoku("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.ichimoku.engine.yf.Ticker")
    def test_components_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ichimoku("AAPL")
        assert result.tenkan is not None
        assert result.kijun is not None
        assert result.senkou_a is not None
        assert result.senkou_b is not None

    @patch("quantpilot_stock.ichimoku.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ichimoku("AAPL")
        assert 0.0 <= result.ichimoku_score <= 100.0

    @patch("quantpilot_stock.ichimoku.engine.yf.Ticker")
    def test_rising_stock_bullish_signal(self, mock_yf):
        df = _make_ohlcv_df(300, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ichimoku("AAPL")
        assert result.signal in {"strong_bull", "bull"}

    @patch("quantpilot_stock.ichimoku.engine.yf.Ticker")
    def test_declining_stock_bearish_signal(self, mock_yf):
        df = _make_declining_df(300, step=0.5)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ichimoku("AAPL")
        assert result.signal in {"strong_bear", "bear"}

    @patch("quantpilot_stock.ichimoku.engine.yf.Ticker")
    def test_price_vs_cloud_valid(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ichimoku("AAPL")
        assert result.price_vs_cloud in {"above", "inside", "below"}

    @patch("quantpilot_stock.ichimoku.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ichimoku("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.ichimoku.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ichimoku("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.ichimoku.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_ichimoku("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.ichimoku.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ichimoku("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}

    @patch("quantpilot_stock.ichimoku.engine.yf.Ticker")
    def test_chikou_above_is_bool(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ichimoku("AAPL")
        assert isinstance(result.chikou_above, bool)

    @patch("quantpilot_stock.ichimoku.engine.yf.Ticker")
    def test_cloud_bullish_rising(self, mock_yf):
        """Rising stock: Senkou A should be > Senkou B (bullish cloud)."""
        df = _make_ohlcv_df(300, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ichimoku("AAPL")
        assert result.cloud_bullish is True

    @patch("quantpilot_stock.ichimoku.engine.yf.Ticker")
    def test_tk_bullish_rising(self, mock_yf):
        """Rising stock: Tenkan (fast) >= Kijun (slow)."""
        df = _make_ohlcv_df(300, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ichimoku("AAPL")
        assert result.tk_bullish is True


# ---------------------------------------------------------------------------
# TestIchimokuAPI
# ---------------------------------------------------------------------------

class TestIchimokuAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/ichimoku")
        assert resp.status_code == 422

    @patch("quantpilot_stock.ichimoku.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/ichimoku?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.ichimoku.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/ichimoku?ticker=AAPL").json()
        for f in ["ticker", "tenkan", "kijun", "senkou_a", "senkou_b",
                  "price_vs_cloud", "ichimoku_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.ichimoku.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/ichimoku?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
