"""Tests for Aroon Indicator — Phase F.53.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from quantpilot_stock.aroon.engine import (
    _classify_signal,
    _compute_aroon_score,
    _compute_aroon_series,
    compute_aroon,
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
# TestComputeAroonSeries
# ---------------------------------------------------------------------------


class TestComputeAroonSeries:
    def test_length_matches_input(self):
        df = _make_ohlcv_df(200)
        up, down, osc = _compute_aroon_series(df["High"], df["Low"])
        assert len(up) == len(down) == len(osc) == 200

    def test_rising_stock_high_aroon_up(self):
        df = _make_ohlcv_df(200, step=1.0)
        up, _, _ = _compute_aroon_series(df["High"], df["Low"])
        # Monotone rising: latest high is the 25-period high → Aroon Up = 100
        assert float(up.iloc[-1]) == pytest.approx(100.0)

    def test_declining_stock_high_aroon_down(self):
        df = _make_declining_df(200)
        _, down, _ = _compute_aroon_series(df["High"], df["Low"])
        # Monotone declining: latest low is the 25-period low → Aroon Down = 100
        assert float(down.iloc[-1]) == pytest.approx(100.0)

    def test_rising_stock_positive_oscillator(self):
        df = _make_ohlcv_df(200, step=1.0)
        _, _, osc = _compute_aroon_series(df["High"], df["Low"])
        assert float(osc.iloc[-1]) > 0.0

    def test_declining_stock_negative_oscillator(self):
        df = _make_declining_df(200)
        _, _, osc = _compute_aroon_series(df["High"], df["Low"])
        assert float(osc.iloc[-1]) < 0.0

    def test_values_in_range(self):
        df = _make_ohlcv_df(200)
        up, down, osc = _compute_aroon_series(df["High"], df["Low"])
        # Drop NaN (first period rows)
        up_clean   = up.dropna()
        down_clean = down.dropna()
        assert float(up_clean.min()) >= 0.0
        assert float(up_clean.max()) <= 100.0
        assert float(down_clean.min()) >= 0.0
        assert float(down_clean.max()) <= 100.0

    def test_oscillator_range(self):
        df = _make_ohlcv_df(200)
        _, _, osc = _compute_aroon_series(df["High"], df["Low"])
        osc_clean = osc.dropna()
        assert float(osc_clean.min()) >= -100.0
        assert float(osc_clean.max()) <= 100.0


# ---------------------------------------------------------------------------
# TestComputeAroonScore
# ---------------------------------------------------------------------------


class TestComputeAroonScore:
    def test_highest_osc_gives_high_score(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        osc = pd.Series([0.0] * 99 + [100.0], index=idx)
        assert _compute_aroon_score(100.0, osc) > 90.0

    def test_lowest_osc_gives_low_score(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        osc = pd.Series([0.0] * 99 + [-100.0], index=idx)
        assert _compute_aroon_score(-100.0, osc) < 10.0

    def test_score_in_range(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        osc = pd.Series(range(-50, 50), dtype=float, index=idx)
        assert 0.0 <= _compute_aroon_score(0.0, osc) <= 100.0

    def test_short_series_fallback(self):
        idx = pd.date_range("2022-01-01", periods=5, freq="B")
        osc = pd.Series([10.0, 20.0, -10.0, 0.0, 5.0], index=idx)
        score = _compute_aroon_score(0.0, osc)
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
# TestComputeAroonIntegration
# ---------------------------------------------------------------------------


class TestComputeAroonIntegration:
    @patch("quantpilot_stock.aroon.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_aroon("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.aroon.engine.yf.Ticker")
    def test_aroon_up_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_aroon("AAPL")
        assert result.aroon_up is not None

    @patch("quantpilot_stock.aroon.engine.yf.Ticker")
    def test_aroon_down_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_aroon("AAPL")
        assert result.aroon_down is not None

    @patch("quantpilot_stock.aroon.engine.yf.Ticker")
    def test_aroon_oscillator_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_aroon("AAPL")
        assert result.aroon_oscillator is not None

    @patch("quantpilot_stock.aroon.engine.yf.Ticker")
    def test_rising_stock_bullish(self, mock_yf):
        df = _make_ohlcv_df(300, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_aroon("AAPL")
        assert result.aroon_bullish is True

    @patch("quantpilot_stock.aroon.engine.yf.Ticker")
    def test_declining_stock_not_bullish(self, mock_yf):
        df = _make_declining_df(300, step=0.3)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_aroon("AAPL")
        assert result.aroon_bullish is False

    @patch("quantpilot_stock.aroon.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_aroon("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.aroon.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_aroon("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.aroon.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_aroon("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.aroon.engine.yf.Ticker")
    def test_score_bounds(self, mock_yf):
        for df in [_make_ohlcv_df(300, step=2.0), _make_declining_df(300)]:
            mock_yf.return_value = _mock_ticker(df)
            result = compute_aroon("AAPL")
            assert 0.0 <= result.aroon_score <= 100.0

    @patch("quantpilot_stock.aroon.engine.yf.Ticker")
    def test_aroon_up_in_range(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_aroon("AAPL")
        assert result.aroon_up is not None
        assert 0.0 <= result.aroon_up <= 100.0

    @patch("quantpilot_stock.aroon.engine.yf.Ticker")
    def test_aroon_down_in_range(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_aroon("AAPL")
        assert result.aroon_down is not None
        assert 0.0 <= result.aroon_down <= 100.0

    @patch("quantpilot_stock.aroon.engine.yf.Ticker")
    def test_oscillator_range(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_aroon("AAPL")
        assert result.aroon_oscillator is not None
        assert -100.0 <= result.aroon_oscillator <= 100.0


# ---------------------------------------------------------------------------
# TestAroonAPI
# ---------------------------------------------------------------------------


class TestAroonAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/aroon")
        assert resp.status_code == 422

    @patch("quantpilot_stock.aroon.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/aroon?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.aroon.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/aroon?ticker=AAPL").json()
        for f in ["ticker", "aroon_up", "aroon_down", "aroon_oscillator",
                  "aroon_bullish", "aroon_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.aroon.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/aroon?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
