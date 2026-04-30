"""Tests for Keltner Channel — Phase F.50.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.keltner.engine import (
    _classify_signal,
    _compute_kc_score,
    _compute_keltner_bands,
    _compute_position,
    compute_keltner,
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
# TestComputeKeltnerBands
# ---------------------------------------------------------------------------


class TestComputeKeltnerBands:
    def test_length_matches_input(self):
        df = _make_ohlcv_df(100)
        upper, middle, lower = _compute_keltner_bands(df["High"], df["Low"], df["Close"])
        assert len(upper) == len(middle) == len(lower) == 100

    def test_upper_above_middle_above_lower(self):
        df = _make_ohlcv_df(100)
        upper, middle, lower = _compute_keltner_bands(df["High"], df["Low"], df["Close"])
        # Check tail where all bands are computed
        assert float(upper.iloc[-1]) > float(middle.iloc[-1]) > float(lower.iloc[-1])

    def test_middle_is_ema_of_close(self):
        """Middle band should be close to the EMA(20) of close."""
        df    = _make_ohlcv_df(100)
        ema20 = df["Close"].ewm(span=20, adjust=False).mean()
        _, middle, _ = _compute_keltner_bands(df["High"], df["Low"], df["Close"])
        assert abs(float(middle.iloc[-1]) - float(ema20.iloc[-1])) < 0.001

    def test_band_width_positive(self):
        df = _make_ohlcv_df(100)
        upper, _, lower = _compute_keltner_bands(df["High"], df["Low"], df["Close"])
        assert float(upper.iloc[-1]) - float(lower.iloc[-1]) > 0.0


# ---------------------------------------------------------------------------
# TestComputePosition
# ---------------------------------------------------------------------------


class TestComputePosition:
    def test_at_lower_band_gives_zero(self):
        idx   = pd.date_range("2022-01-01", periods=5, freq="B")
        close = pd.Series([100.0] * 5, index=idx)
        upper = pd.Series([110.0] * 5, index=idx)
        lower = pd.Series([100.0] * 5, index=idx)
        pos   = _compute_position(close, upper, lower)
        assert abs(float(pos.iloc[-1]) - 0.0) < 0.001

    def test_at_upper_band_gives_100(self):
        idx   = pd.date_range("2022-01-01", periods=5, freq="B")
        close = pd.Series([110.0] * 5, index=idx)
        upper = pd.Series([110.0] * 5, index=idx)
        lower = pd.Series([100.0] * 5, index=idx)
        pos   = _compute_position(close, upper, lower)
        assert abs(float(pos.iloc[-1]) - 100.0) < 0.001

    def test_at_midpoint_gives_50(self):
        idx   = pd.date_range("2022-01-01", periods=5, freq="B")
        close = pd.Series([105.0] * 5, index=idx)
        upper = pd.Series([110.0] * 5, index=idx)
        lower = pd.Series([100.0] * 5, index=idx)
        pos   = _compute_position(close, upper, lower)
        assert abs(float(pos.iloc[-1]) - 50.0) < 0.001

    def test_above_upper_clipped_to_100(self):
        idx   = pd.date_range("2022-01-01", periods=5, freq="B")
        close = pd.Series([120.0] * 5, index=idx)
        upper = pd.Series([110.0] * 5, index=idx)
        lower = pd.Series([100.0] * 5, index=idx)
        pos   = _compute_position(close, upper, lower)
        assert float(pos.iloc[-1]) <= 100.0

    def test_below_lower_clipped_to_zero(self):
        idx   = pd.date_range("2022-01-01", periods=5, freq="B")
        close = pd.Series([90.0] * 5, index=idx)
        upper = pd.Series([110.0] * 5, index=idx)
        lower = pd.Series([100.0] * 5, index=idx)
        pos   = _compute_position(close, upper, lower)
        assert float(pos.iloc[-1]) >= 0.0


# ---------------------------------------------------------------------------
# TestComputeKCScore
# ---------------------------------------------------------------------------


class TestComputeKCScore:
    def test_high_position_gives_high_score(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        pos = pd.Series([50.0] * 99 + [99.0], index=idx)
        assert _compute_kc_score(99.0, pos) > 90.0

    def test_low_position_gives_low_score(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        pos = pd.Series([50.0] * 99 + [1.0], index=idx)
        assert _compute_kc_score(1.0, pos) < 10.0

    def test_score_in_range(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        pos = pd.Series(range(100), dtype=float, index=idx)
        assert 0.0 <= _compute_kc_score(50.0, pos) <= 100.0

    def test_short_series_fallback(self):
        idx = pd.date_range("2022-01-01", periods=5, freq="B")
        pos = pd.Series([10.0, 30.0, 50.0, 70.0, 90.0], index=idx)
        assert 0.0 <= _compute_kc_score(50.0, pos) <= 100.0


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
# TestComputeKeltnerIntegration
# ---------------------------------------------------------------------------


class TestComputeKeltnerIntegration:
    @patch("quantpilot_stock.keltner.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_keltner("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.keltner.engine.yf.Ticker")
    def test_bands_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_keltner("AAPL")
        assert result.upper is not None
        assert result.middle is not None
        assert result.lower is not None

    @patch("quantpilot_stock.keltner.engine.yf.Ticker")
    def test_upper_above_middle_above_lower(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_keltner("AAPL")
        assert result.upper > result.middle > result.lower  # type: ignore[operator]

    @patch("quantpilot_stock.keltner.engine.yf.Ticker")
    def test_rising_stock_above_upper_or_high_position(self, mock_yf):
        """Fast-rising stock should be near or above upper Keltner band."""
        df = _make_ohlcv_df(300, step=2.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_keltner("AAPL")
        assert result.kc_position is not None and result.kc_position >= 50.0

    @patch("quantpilot_stock.keltner.engine.yf.Ticker")
    def test_declining_stock_below_lower_or_low_position(self, mock_yf):
        df = _make_declining_df(300, step=2.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_keltner("AAPL")
        assert result.kc_position is not None and result.kc_position <= 50.0

    @patch("quantpilot_stock.keltner.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_keltner("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.keltner.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_keltner("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.keltner.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_keltner("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.keltner.engine.yf.Ticker")
    def test_score_bounds(self, mock_yf):
        for df in [_make_ohlcv_df(300, step=2.0), _make_declining_df(300)]:
            mock_yf.return_value = _mock_ticker(df)
            result = compute_keltner("AAPL")
            assert 0.0 <= result.kc_score <= 100.0

    @patch("quantpilot_stock.keltner.engine.yf.Ticker")
    def test_channel_width_positive(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_keltner("AAPL")
        assert result.channel_width_pct is not None and result.channel_width_pct > 0.0


# ---------------------------------------------------------------------------
# TestKeltnerAPI
# ---------------------------------------------------------------------------


class TestKeltnerAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/keltner")
        assert resp.status_code == 422

    @patch("quantpilot_stock.keltner.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/keltner?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.keltner.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/keltner?ticker=AAPL").json()
        for f in ["ticker", "upper", "middle", "lower", "kc_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.keltner.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/keltner?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
