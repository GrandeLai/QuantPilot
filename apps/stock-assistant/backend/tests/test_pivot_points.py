"""Tests for Pivot Points — F.85.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.pivot_points.engine import (
    _classify_signal,
    _compute_pivot_levels,
    compute_pivot_points,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv_df(
    n: int,
    start: float = 100.0,
    step: float = 0.5,
) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [start + i * step for i in range(n)]
    return pd.DataFrame(
        {
            "Open":   closes,
            "High":   [c + 2.0 for c in closes],
            "Low":    [c - 2.0 for c in closes],
            "Close":  closes,
            "Volume": [1_000_000] * n,
        },
        index=idx,
    )


def _make_declining_df(n: int, start: float = 200.0, step: float = 0.5) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [start - i * step for i in range(n)]
    return pd.DataFrame(
        {
            "Open":   closes,
            "High":   [c + 2.0 for c in closes],
            "Low":    [c - 2.0 for c in closes],
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
# TestComputePivotLevels
# ---------------------------------------------------------------------------

class TestComputePivotLevels:
    def test_pp_is_average(self):
        pp, _, _, _, _, _, _ = _compute_pivot_levels(110.0, 90.0, 100.0)
        expected = (110.0 + 90.0 + 100.0) / 3.0
        assert abs(pp - expected) < 1e-9

    def test_r1_above_pp(self):
        pp, r1, _, _, _, _, _ = _compute_pivot_levels(110.0, 90.0, 100.0)
        assert r1 > pp

    def test_s1_below_pp(self):
        pp, _, _, _, s1, _, _ = _compute_pivot_levels(110.0, 90.0, 100.0)
        assert s1 < pp

    def test_r2_above_r1(self):
        _, r1, r2, _, _, _, _ = _compute_pivot_levels(110.0, 90.0, 100.0)
        assert r2 > r1

    def test_s2_below_s1(self):
        _, _, _, _, s1, s2, _ = _compute_pivot_levels(110.0, 90.0, 100.0)
        assert s2 < s1

    def test_r3_above_r2(self):
        _, _, r2, r3, _, _, _ = _compute_pivot_levels(110.0, 90.0, 100.0)
        assert r3 > r2

    def test_s3_below_s2(self):
        _, _, _, _, _, s2, s3 = _compute_pivot_levels(110.0, 90.0, 100.0)
        assert s3 < s2

    def test_symmetry_r1_s1(self):
        """R1 and S1 are equidistant from PP in opposite directions."""
        pp, r1, _, _, s1, _, _ = _compute_pivot_levels(110.0, 90.0, 100.0)
        assert abs((r1 - pp) - (pp - s1)) < 1e-9

    def test_specific_values(self):
        """Manual calculation check."""
        # H=120, L=100, C=110 → PP=(330/3)=110, R1=2*110-100=120, S1=2*110-120=100
        pp, r1, _, _, s1, _, _ = _compute_pivot_levels(120.0, 100.0, 110.0)
        assert abs(pp - 110.0) < 1e-9
        assert abs(r1 - 120.0) < 1e-9
        assert abs(s1 - 100.0) < 1e-9


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


# ---------------------------------------------------------------------------
# TestComputePivotPointsIntegration
# ---------------------------------------------------------------------------

class TestComputePivotPointsIntegration:
    @patch("quantpilot_stock.pivot_points.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(50)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_pivot_points("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.pivot_points.engine.yf.Ticker")
    def test_all_levels_populated(self, mock_yf):
        df = _make_ohlcv_df(50)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_pivot_points("AAPL")
        for field in [result.pp, result.r1, result.r2, result.r3,
                      result.s1, result.s2, result.s3, result.close]:
            assert field is not None

    @patch("quantpilot_stock.pivot_points.engine.yf.Ticker")
    def test_level_ordering(self, mock_yf):
        df = _make_ohlcv_df(50)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_pivot_points("AAPL")
        assert result.r3 > result.r2 > result.r1 > result.pp > result.s1 > result.s2 > result.s3  # type: ignore[operator]

    @patch("quantpilot_stock.pivot_points.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(50)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_pivot_points("AAPL")
        assert 0.0 <= result.pivot_score <= 100.0

    @patch("quantpilot_stock.pivot_points.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(50)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_pivot_points("AAPL")
        valid = {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}
        assert result.signal in valid

    @patch("quantpilot_stock.pivot_points.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(50)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_pivot_points("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.pivot_points.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(3)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_pivot_points("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.pivot_points.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_pivot_points("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"


# ---------------------------------------------------------------------------
# TestPivotPointsAPI
# ---------------------------------------------------------------------------

class TestPivotPointsAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/pivot_points")
        assert resp.status_code == 422

    @patch("quantpilot_stock.pivot_points.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(50)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/pivot_points?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.pivot_points.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(50)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/pivot_points?ticker=AAPL").json()
        for f in ["ticker", "pp", "r1", "r2", "r3", "s1", "s2", "s3",
                  "close", "pivot_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.pivot_points.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/pivot_points?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
