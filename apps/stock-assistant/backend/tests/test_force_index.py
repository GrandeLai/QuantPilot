"""Tests for Force Index — Phase F.51.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.force_index.engine import (
    _classify_signal,
    _compute_fi_direction,
    _compute_fi_score,
    _compute_fi_series,
    compute_force_index,
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
# TestComputeFISeries
# ---------------------------------------------------------------------------


class TestComputeFISeries:
    def test_length_matches_input(self):
        df = _make_ohlcv_df(100)
        fi = _compute_fi_series(df["Close"], df["Volume"])
        assert len(fi) == 100

    def test_rising_stock_positive_fi(self):
        df = _make_ohlcv_df(100, step=1.0)
        fi = _compute_fi_series(df["Close"], df["Volume"])
        assert float(fi.iloc[-1]) > 0.0

    def test_declining_stock_negative_fi(self):
        df = _make_declining_df(100, step=1.0)
        fi = _compute_fi_series(df["Close"], df["Volume"])
        assert float(fi.iloc[-1]) < 0.0

    def test_flat_stock_near_zero_fi(self):
        idx    = pd.date_range("2022-01-01", periods=50, freq="B")
        close  = pd.Series([100.0] * 50, index=idx)
        volume = pd.Series([1_000_000] * 50, index=idx)
        fi     = _compute_fi_series(close, volume)
        assert abs(float(fi.iloc[-1])) < 1.0

    def test_known_value(self):
        """FI = diff × volume; single step of +1 × 1M = 1_000_000."""
        idx    = pd.date_range("2022-01-01", periods=2, freq="B")
        close  = pd.Series([100.0, 101.0], index=idx)
        volume = pd.Series([1_000_000, 1_000_000], index=idx)
        fi     = _compute_fi_series(close, volume, ema_period=1)
        # EMA period=1 → no smoothing, last value = last raw
        assert abs(float(fi.iloc[-1]) - 1_000_000.0) < 1.0

    def test_high_volume_amplifies_force(self):
        """Same price move, higher volume → larger |FI|."""
        idx = pd.date_range("2022-01-01", periods=50, freq="B")
        c   = pd.Series([100.0 + i for i in range(50)], index=idx)
        v1  = pd.Series([1_000_000] * 50, index=idx)
        v2  = pd.Series([5_000_000] * 50, index=idx)
        fi1 = _compute_fi_series(c, v1)
        fi2 = _compute_fi_series(c, v2)
        assert abs(float(fi2.iloc[-1])) > abs(float(fi1.iloc[-1]))


# ---------------------------------------------------------------------------
# TestComputeFIDirection
# ---------------------------------------------------------------------------


class TestComputeFIDirection:
    def test_increasing_fi_rising(self):
        idx = pd.date_range("2022-01-01", periods=5, freq="B")
        fi  = pd.Series([100.0, 200.0, 300.0, 400.0, 500.0], index=idx)
        assert _compute_fi_direction(fi) == "rising"

    def test_decreasing_fi_falling(self):
        idx = pd.date_range("2022-01-01", periods=5, freq="B")
        fi  = pd.Series([500.0, 400.0, 300.0, 200.0, 100.0], index=idx)
        assert _compute_fi_direction(fi) == "falling"

    def test_single_bar_flat(self):
        idx = pd.date_range("2022-01-01", periods=1, freq="B")
        fi  = pd.Series([100.0], index=idx)
        assert _compute_fi_direction(fi) == "flat"


# ---------------------------------------------------------------------------
# TestComputeFIScore
# ---------------------------------------------------------------------------


class TestComputeFIScore:
    def test_highest_fi_gives_high_score(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        fi  = pd.Series([0.0] * 99 + [1e9], index=idx)
        assert _compute_fi_score(1e9, fi) > 90.0

    def test_lowest_fi_gives_low_score(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        fi  = pd.Series([0.0] * 99 + [-1e9], index=idx)
        assert _compute_fi_score(-1e9, fi) < 10.0

    def test_score_in_range(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        fi  = pd.Series(range(100), dtype=float, index=idx)
        assert 0.0 <= _compute_fi_score(50.0, fi) <= 100.0


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
# TestComputeForceIndexIntegration
# ---------------------------------------------------------------------------


class TestComputeForceIndexIntegration:
    @patch("quantpilot_stock.force_index.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_force_index("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.force_index.engine.yf.Ticker")
    def test_force_index_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_force_index("AAPL")
        assert result.force_index is not None

    @patch("quantpilot_stock.force_index.engine.yf.Ticker")
    def test_rising_stock_positive_fi(self, mock_yf):
        df = _make_ohlcv_df(300, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_force_index("AAPL")
        assert result.fi_positive is True

    @patch("quantpilot_stock.force_index.engine.yf.Ticker")
    def test_declining_stock_negative_fi(self, mock_yf):
        df = _make_declining_df(300, step=0.5)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_force_index("AAPL")
        assert result.fi_positive is False

    @patch("quantpilot_stock.force_index.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_force_index("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.force_index.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_force_index("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.force_index.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_force_index("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.force_index.engine.yf.Ticker")
    def test_score_bounds(self, mock_yf):
        for df in [_make_ohlcv_df(300, step=2.0), _make_declining_df(300)]:
            mock_yf.return_value = _mock_ticker(df)
            result = compute_force_index("AAPL")
            assert 0.0 <= result.fi_score <= 100.0

    @patch("quantpilot_stock.force_index.engine.yf.Ticker")
    def test_direction_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_force_index("AAPL")
        assert result.fi_direction in ("rising", "falling", "flat")


# ---------------------------------------------------------------------------
# TestForceIndexAPI
# ---------------------------------------------------------------------------


class TestForceIndexAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/force-index")
        assert resp.status_code == 422

    @patch("quantpilot_stock.force_index.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/force-index?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.force_index.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/force-index?ticker=AAPL").json()
        for f in ["ticker", "force_index", "fi_positive", "fi_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.force_index.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/force-index?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
