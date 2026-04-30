"""Tests for Mass Index — Phase F.67.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.mass_index.engine import (
    _classify_signal,
    _compute_mi_score,
    _compute_mi_series,
    _detect_reversal,
    compute_mass_index,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv_df(n: int, start: float = 100.0, step: float = 0.5) -> pd.DataFrame:
    idx    = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [start + i * step for i in range(n)]
    return pd.DataFrame(
        {
            "Open":   closes,
            "High":   [c + 1.5 for c in closes],
            "Low":    [c - 1.5 for c in closes],
            "Close":  closes,
            "Volume": [1_000_000] * n,
        },
        index=idx,
    )


def _make_volatile_df(n: int, amplitude: float = 5.0) -> pd.DataFrame:
    """High-amplitude swings to push MI into the bulge zone."""
    idx    = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [100.0] * n
    return pd.DataFrame(
        {
            "Open":   closes,
            "High":   [c + amplitude for c in closes],
            "Low":    [c - amplitude for c in closes],
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
# TestComputeMISeries
# ---------------------------------------------------------------------------

class TestComputeMISeries:
    def test_returns_series(self):
        df = _make_ohlcv_df(200)
        mi = _compute_mi_series(df["High"], df["Low"])
        assert isinstance(mi, pd.Series)

    def test_length_matches_input(self):
        df = _make_ohlcv_df(200)
        mi = _compute_mi_series(df["High"], df["Low"])
        assert len(mi) == 200

    def test_mi_positive(self):
        """Mass Index is always positive (it's a sum of ratios ≥ 1)."""
        df = _make_ohlcv_df(200)
        mi = _compute_mi_series(df["High"], df["Low"])
        assert float(mi.iloc[-1]) > 0.0

    def test_volatile_market_higher_mi(self):
        """Expanding amplitude → EMA1 rises faster than EMA2 → MI above 25."""
        idx = pd.date_range("2022-01-01", periods=200, freq="B")
        # Amplitude increases from 0.1 to 20 over 200 bars
        amplitudes = [0.1 + i * 0.1 for i in range(200)]
        high = pd.Series([100.0 + a for a in amplitudes], index=idx)
        low  = pd.Series([100.0 - a for a in amplitudes], index=idx)
        mi   = _compute_mi_series(high, low)
        # With an expanding HL range, EMA1 > EMA2 (fast EMA tracks expansion)
        # so ratio > 1 and MI > sum_period (25)
        assert float(mi.iloc[-1]) > 25.0

    def test_no_inf_values(self):
        import math
        df = _make_ohlcv_df(200)
        mi = _compute_mi_series(df["High"], df["Low"])
        assert all(math.isfinite(v) for v in mi.dropna().values)

    def test_flat_hl_gives_constant_ratio(self):
        """When High==Low (zero range), EMA1==EMA2, ratio==1, MI==sum_period."""
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        high = pd.Series([100.0] * 100, index=idx)
        low  = pd.Series([100.0] * 100, index=idx)
        mi   = _compute_mi_series(high, low)
        assert abs(float(mi.iloc[-1]) - 25.0) < 0.01


# ---------------------------------------------------------------------------
# TestDetectReversal
# ---------------------------------------------------------------------------

class TestDetectReversal:
    def _make_series(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_no_reversal_all_calm(self):
        s = self._make_series([25.0] * 20)
        assert _detect_reversal(s) is False

    def test_reversal_detected(self):
        # Goes above 27, then drops below 26.5
        vals = [25.0] * 8 + [27.5] + [26.0]
        s = self._make_series(vals)
        assert _detect_reversal(s) is True

    def test_no_reversal_still_above(self):
        # Went above 27 but hasn't dropped below 26.5 yet
        vals = [25.0] * 8 + [27.5, 27.2]
        s = self._make_series(vals)
        assert _detect_reversal(s) is False


# ---------------------------------------------------------------------------
# TestComputeMIScore
# ---------------------------------------------------------------------------

class TestComputeMIScore:
    def _make_series(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_calm_market_high_score(self):
        """MI well below 26.5 and declining → high score."""
        s = self._make_series([26.0, 25.8, 25.6, 25.4, 25.2, 25.0])
        score = _compute_mi_score(25.0, s)
        assert score >= 60.0

    def test_score_in_range(self):
        s = self._make_series([float(i) for i in range(24, 30)])
        for mi in [25.0, 27.5]:
            score = _compute_mi_score(mi, s)
            assert 0.0 <= score <= 100.0

    def test_short_series_fallback(self):
        s = self._make_series([25.0, 26.0])
        score = _compute_mi_score(25.0, s)
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
# TestComputeMassIndexIntegration
# ---------------------------------------------------------------------------

class TestComputeMassIndexIntegration:
    @patch("quantpilot_stock.mass_index.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_mass_index("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.mass_index.engine.yf.Ticker")
    def test_fields_populated(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_mass_index("AAPL")
        assert result.mass_index is not None
        assert result.mass_index > 0
        assert isinstance(result.in_bulge, bool)
        assert isinstance(result.trending_down, bool)

    @patch("quantpilot_stock.mass_index.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_mass_index("AAPL")
        assert 0.0 <= result.mi_score <= 100.0

    @patch("quantpilot_stock.mass_index.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_mass_index("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.mass_index.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_mass_index("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.mass_index.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_mass_index("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.mass_index.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_mass_index("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}


# ---------------------------------------------------------------------------
# TestMassIndexAPI
# ---------------------------------------------------------------------------

class TestMassIndexAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/mass_index")
        assert resp.status_code == 422

    @patch("quantpilot_stock.mass_index.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/mass_index?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.mass_index.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(300)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/mass_index?ticker=AAPL").json()
        for f in ["ticker", "mass_index", "in_bulge", "trending_down",
                  "reversal_signal", "mi_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.mass_index.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/mass_index?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
