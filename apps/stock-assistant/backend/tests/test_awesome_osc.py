"""Tests for Awesome Oscillator — F.78.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.awesome_osc.engine import (
    _classify_signal,
    _compute_ao_score,
    _compute_ao_series,
    compute_ao,
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
            "High":   [c + 1.0 for c in closes],
            "Low":    [c - 1.0 for c in closes],
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
# TestComputeAOSeries
# ---------------------------------------------------------------------------

class TestComputeAOSeries:
    def test_returns_series(self):
        df = _make_ohlcv_df(200)
        ao = _compute_ao_series(df["High"], df["Low"])
        assert isinstance(ao, pd.Series)

    def test_length_matches_input(self):
        df = _make_ohlcv_df(200)
        ao = _compute_ao_series(df["High"], df["Low"])
        assert len(ao) == 200

    def test_no_nan_at_end(self):
        df = _make_ohlcv_df(200)
        ao = _compute_ao_series(df["High"], df["Low"])
        assert not pd.isna(ao.iloc[-1])

    def test_rising_market_positive_ao(self):
        """Rising price → faster SMA > slower SMA → AO > 0."""
        df = _make_ohlcv_df(200, step=1.0)
        ao = _compute_ao_series(df["High"], df["Low"])
        assert float(ao.iloc[-1]) > 0.0

    def test_declining_market_negative_ao(self):
        """Declining price → faster SMA < slower SMA → AO < 0."""
        df = _make_declining_df(200, step=1.0)
        ao = _compute_ao_series(df["High"], df["Low"])
        assert float(ao.iloc[-1]) < 0.0

    def test_flat_market_near_zero_ao(self):
        """Flat price → SMA(5) ≈ SMA(34) → AO ≈ 0."""
        n = 200
        idx = pd.date_range("2022-01-01", periods=n, freq="B")
        high = pd.Series([101.0] * n, index=idx)
        low = pd.Series([99.0] * n, index=idx)
        ao = _compute_ao_series(high, low)
        assert abs(float(ao.iloc[-1])) < 0.1

    def test_no_inf_values(self):
        import math
        df = _make_ohlcv_df(200)
        ao = _compute_ao_series(df["High"], df["Low"])
        assert all(math.isfinite(v) for v in ao.dropna())

    def test_custom_periods(self):
        df = _make_ohlcv_df(200)
        ao_default = _compute_ao_series(df["High"], df["Low"])
        ao_custom = _compute_ao_series(df["High"], df["Low"], fast=3, slow=20)
        assert len(ao_default) == len(ao_custom) == 200


# ---------------------------------------------------------------------------
# TestComputeAOScore
# ---------------------------------------------------------------------------

class TestComputeAOScore:
    def _make_ao(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_positive_rising_ao_scores_high(self):
        ao = self._make_ao([1.0 + i * 0.01 for i in range(200)])
        score = _compute_ao_score(ao)
        assert score >= 60.0

    def test_negative_falling_ao_scores_low(self):
        ao = self._make_ao([-1.0 - i * 0.01 for i in range(200)])
        score = _compute_ao_score(ao)
        assert score < 40.0

    def test_score_in_range(self):
        for vals in [[0.0] * 200, [1.0] * 200, [-1.0] * 200]:
            ao = self._make_ao(vals)
            score = _compute_ao_score(ao)
            assert 0.0 <= score <= 100.0

    def test_single_bar_fallback(self):
        ao = self._make_ao([1.0])
        score = _compute_ao_score(ao)
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

    def test_boundary_20(self):
        assert _classify_signal(20.0) == "bear"


# ---------------------------------------------------------------------------
# TestComputeAOIntegration
# ---------------------------------------------------------------------------

class TestComputeAOIntegration:
    @patch("quantpilot_stock.awesome_osc.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ao("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.awesome_osc.engine.yf.Ticker")
    def test_fields_populated(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ao("AAPL")
        assert result.ao_value is not None
        assert isinstance(result.ao_positive, bool)
        assert isinstance(result.ao_rising, bool)

    @patch("quantpilot_stock.awesome_osc.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ao("AAPL")
        assert 0.0 <= result.ao_score <= 100.0

    @patch("quantpilot_stock.awesome_osc.engine.yf.Ticker")
    def test_rising_market_ao_positive(self, mock_yf):
        df = _make_ohlcv_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ao("AAPL")
        assert result.ao_positive is True

    @patch("quantpilot_stock.awesome_osc.engine.yf.Ticker")
    def test_declining_market_ao_negative(self, mock_yf):
        df = _make_declining_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ao("AAPL")
        assert result.ao_positive is False

    @patch("quantpilot_stock.awesome_osc.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ao("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}

    @patch("quantpilot_stock.awesome_osc.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ao("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.awesome_osc.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_ao("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.awesome_osc.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_ao("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"


# ---------------------------------------------------------------------------
# TestAOAPI
# ---------------------------------------------------------------------------

class TestAOAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/awesome_osc")
        assert resp.status_code == 422

    @patch("quantpilot_stock.awesome_osc.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/awesome_osc?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.awesome_osc.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/awesome_osc?ticker=AAPL").json()
        for f in ["ticker", "ao_value", "ao_positive", "ao_rising",
                  "ao_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.awesome_osc.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/awesome_osc?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
