"""Tests for Donchian Channels — Phase F.58.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from quantpilot_stock.donchian.engine import (
    _classify_signal,
    _compute_donchian_score,
    _compute_donchian_series,
    compute_donchian,
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
# TestComputeDonchianSeries
# ---------------------------------------------------------------------------


class TestComputeDonchianSeries:
    def test_length_matches_input(self):
        df = _make_ohlcv_df(200)
        upper, lower, mid, pos = _compute_donchian_series(df["High"], df["Low"], df["Close"])
        assert len(upper) == len(lower) == len(mid) == len(pos) == 200

    def test_upper_ge_lower(self):
        df = _make_ohlcv_df(200)
        upper, lower, _, _ = _compute_donchian_series(df["High"], df["Low"], df["Close"])
        upper_clean = upper.dropna()
        lower_clean = lower.dropna()
        assert (upper_clean.values >= lower_clean.values).all()

    def test_rising_stock_high_position(self):
        """Rising stock: close near upper band → position close to 100."""
        df = _make_ohlcv_df(200, step=1.0)
        _, _, _, pos = _compute_donchian_series(df["High"], df["Low"], df["Close"])
        assert float(pos.iloc[-1]) > 50.0

    def test_declining_stock_low_position(self):
        """Declining stock: close near lower band → position close to 0."""
        df = _make_declining_df(200, step=1.0)
        _, _, _, pos = _compute_donchian_series(df["High"], df["Low"], df["Close"])
        assert float(pos.iloc[-1]) < 50.0

    def test_position_in_range(self):
        df = _make_ohlcv_df(200)
        _, _, _, pos = _compute_donchian_series(df["High"], df["Low"], df["Close"])
        pos_clean = pos.dropna()
        assert float(pos_clean.min()) >= 0.0
        assert float(pos_clean.max()) <= 100.0

    def test_middle_between_bands(self):
        df = _make_ohlcv_df(200)
        upper, lower, mid, _ = _compute_donchian_series(df["High"], df["Low"], df["Close"])
        upper_clean = upper.dropna()
        lower_clean = lower.dropna()
        mid_clean   = mid.dropna()
        expected    = (upper_clean + lower_clean) / 2
        assert (abs(mid_clean - expected) < 0.001).all()


# ---------------------------------------------------------------------------
# TestComputeDonchianScore
# ---------------------------------------------------------------------------


class TestComputeDonchianScore:
    def test_highest_pos_gives_high_score(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        pos = pd.Series([50.0] * 99 + [100.0], index=idx)
        assert _compute_donchian_score(100.0, pos) > 90.0

    def test_lowest_pos_gives_low_score(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        pos = pd.Series([50.0] * 99 + [0.0], index=idx)
        assert _compute_donchian_score(0.0, pos) < 10.0

    def test_score_in_range(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        pos = pd.Series(range(100), dtype=float, index=idx)
        assert 0.0 <= _compute_donchian_score(50.0, pos) <= 100.0

    def test_short_series_fallback(self):
        idx = pd.date_range("2022-01-01", periods=5, freq="B")
        pos = pd.Series([40.0, 60.0, 50.0, 70.0, 30.0], index=idx)
        score = _compute_donchian_score(50.0, pos)
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
# TestComputeDonchianIntegration
# ---------------------------------------------------------------------------


class TestComputeDonchianIntegration:
    @patch("quantpilot_stock.donchian.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_donchian("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.donchian.engine.yf.Ticker")
    def test_upper_lower_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_donchian("AAPL")
        assert result.upper is not None
        assert result.lower is not None

    @patch("quantpilot_stock.donchian.engine.yf.Ticker")
    def test_upper_ge_lower(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_donchian("AAPL")
        assert result.upper is not None and result.lower is not None
        assert result.upper >= result.lower

    @patch("quantpilot_stock.donchian.engine.yf.Ticker")
    def test_position_in_range(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_donchian("AAPL")
        assert result.position is not None
        assert 0.0 <= result.position <= 100.0

    @patch("quantpilot_stock.donchian.engine.yf.Ticker")
    def test_rising_stock_high_position(self, mock_yf):
        df = _make_ohlcv_df(300, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_donchian("AAPL")
        assert result.position is not None
        assert result.position > 50.0

    @patch("quantpilot_stock.donchian.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_donchian("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.donchian.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_donchian("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.donchian.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_donchian("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.donchian.engine.yf.Ticker")
    def test_score_bounds(self, mock_yf):
        for df in [_make_ohlcv_df(300, step=2.0), _make_declining_df(300)]:
            mock_yf.return_value = _mock_ticker(df)
            result = compute_donchian("AAPL")
            assert 0.0 <= result.donchian_score <= 100.0

    @patch("quantpilot_stock.donchian.engine.yf.Ticker")
    def test_channel_width_positive(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_donchian("AAPL")
        assert result.channel_width_pct is not None
        assert result.channel_width_pct >= 0.0

    @patch("quantpilot_stock.donchian.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_donchian("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}


# ---------------------------------------------------------------------------
# TestDonchianAPI
# ---------------------------------------------------------------------------


class TestDonchianAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/donchian")
        assert resp.status_code == 422

    @patch("quantpilot_stock.donchian.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/donchian?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.donchian.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/donchian?ticker=AAPL").json()
        for f in ["ticker", "upper", "lower", "middle", "position",
                  "channel_width_pct", "donchian_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.donchian.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/donchian?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False

    @pytest.mark.parametrize("step,expected_signal", [
        (2.0, True),   # rising: high position → bullish score
        (0.3, True),   # slow rising: still positive
    ])
    @patch("quantpilot_stock.donchian.engine.yf.Ticker")
    def test_rising_stock_position_above_50(self, mock_yf, step, expected_signal):
        df = _make_ohlcv_df(300, step=step)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_donchian("AAPL")
        assert result.position is not None
        if expected_signal:
            assert result.position > 50.0
