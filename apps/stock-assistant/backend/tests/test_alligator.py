"""Tests for Williams Alligator — F.77.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.alligator.engine import (
    _classify_signal,
    _compute_alligator_score,
    _compute_alligator_series,
    _compute_smma,
    compute_alligator,
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
# TestComputeSMMA
# ---------------------------------------------------------------------------

class TestComputeSMMA:
    def test_returns_series(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        s = pd.Series([100.0] * 100, index=idx)
        result = _compute_smma(s, 13)
        assert isinstance(result, pd.Series)

    def test_constant_series_unchanged(self):
        idx = pd.date_range("2022-01-01", periods=100, freq="B")
        s = pd.Series([100.0] * 100, index=idx)
        result = _compute_smma(s, 13)
        assert abs(float(result.iloc[-1]) - 100.0) < 0.01

    def test_length_preserved(self):
        idx = pd.date_range("2022-01-01", periods=200, freq="B")
        s = pd.Series(range(200), dtype=float, index=idx)
        result = _compute_smma(s, 5)
        assert len(result) == 200


# ---------------------------------------------------------------------------
# TestComputeAlligatorSeries
# ---------------------------------------------------------------------------

class TestComputeAlligatorSeries:
    def test_returns_three_series(self):
        df = _make_ohlcv_df(200)
        jaw, teeth, lips = _compute_alligator_series(df["High"], df["Low"])
        assert isinstance(jaw, pd.Series)
        assert isinstance(teeth, pd.Series)
        assert isinstance(lips, pd.Series)

    def test_all_same_length(self):
        df = _make_ohlcv_df(200)
        jaw, teeth, lips = _compute_alligator_series(df["High"], df["Low"])
        assert len(jaw) == len(teeth) == len(lips) == 200

    def test_no_nan_at_end(self):
        df = _make_ohlcv_df(200)
        jaw, teeth, lips = _compute_alligator_series(df["High"], df["Low"])
        assert not pd.isna(jaw.iloc[-1])
        assert not pd.isna(teeth.iloc[-1])
        assert not pd.isna(lips.iloc[-1])

    def test_rising_market_lips_above_jaw(self):
        """In a rising market, faster MA (lips) should be above slower (jaw)."""
        df = _make_ohlcv_df(200, step=1.0)
        jaw, teeth, lips = _compute_alligator_series(df["High"], df["Low"])
        assert float(lips.iloc[-1]) > float(jaw.iloc[-1])

    def test_declining_market_lips_below_jaw(self):
        """In a declining market, faster MA (lips) should be below slower (jaw)."""
        df = _make_declining_df(200, step=1.0)
        jaw, teeth, lips = _compute_alligator_series(df["High"], df["Low"])
        assert float(lips.iloc[-1]) < float(jaw.iloc[-1])

    def test_lips_fastest_ma(self):
        """Lips (SMMA 5) is more responsive than jaw (SMMA 13)."""
        df = _make_ohlcv_df(200, step=1.0)
        jaw, _, lips = _compute_alligator_series(df["High"], df["Low"])
        # Lips is closer to current price → higher value in uptrend
        median = (df["High"] + df["Low"]) / 2.0
        lips_diff = abs(float(lips.iloc[-1]) - float(median.iloc[-1]))
        jaw_diff = abs(float(jaw.iloc[-1]) - float(median.iloc[-1]))
        assert lips_diff <= jaw_diff


# ---------------------------------------------------------------------------
# TestComputeAlligatorScore
# ---------------------------------------------------------------------------

class TestComputeAlligatorScore:
    def _make_series(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_fully_bullish_scores_high(self):
        """lips > teeth > jaw + price above jaw + jaw rising → high score."""
        jaw = self._make_series([90.0 + i * 0.05 for i in range(200)])
        lips = self._make_series([100.0 + i * 0.1 for i in range(200)])
        score = _compute_alligator_score(
            110.0, 90.25, 95.0, 100.0, jaw, lips
        )
        assert score >= 60.0

    def test_fully_bearish_scores_low(self):
        """lips < teeth < jaw + price below jaw → low score."""
        jaw = self._make_series([100.0 - i * 0.05 for i in range(200)])
        lips = self._make_series([80.0 - i * 0.1 for i in range(200)])
        score = _compute_alligator_score(
            60.0, 99.75, 90.0, 80.0, jaw, lips
        )
        assert score < 40.0

    def test_score_in_range(self):
        jaw = self._make_series([100.0] * 200)
        lips = self._make_series([105.0] * 200)
        score = _compute_alligator_score(102.0, 100.0, 103.0, 105.0, jaw, lips)
        assert 0.0 <= score <= 100.0

    def test_short_series_fallback(self):
        jaw = self._make_series([100.0, 101.0])
        lips = self._make_series([105.0, 106.0])
        score = _compute_alligator_score(110.0, 100.0, 103.0, 105.0, jaw, lips)
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
# TestComputeAlligatorIntegration
# ---------------------------------------------------------------------------

class TestComputeAlligatorIntegration:
    @patch("quantpilot_stock.alligator.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_alligator("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.alligator.engine.yf.Ticker")
    def test_fields_populated(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_alligator("AAPL")
        assert result.jaw is not None
        assert result.teeth is not None
        assert result.lips is not None
        assert isinstance(result.lips_above_teeth, bool)
        assert isinstance(result.teeth_above_jaw, bool)

    @patch("quantpilot_stock.alligator.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_alligator("AAPL")
        assert 0.0 <= result.alligator_score <= 100.0

    @patch("quantpilot_stock.alligator.engine.yf.Ticker")
    def test_rising_market_bullish_alignment(self, mock_yf):
        """Rising market: lips > teeth > jaw."""
        df = _make_ohlcv_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_alligator("AAPL")
        assert result.lips_above_teeth is True
        assert result.teeth_above_jaw is True

    @patch("quantpilot_stock.alligator.engine.yf.Ticker")
    def test_declining_market_bearish_alignment(self, mock_yf):
        """Declining market: lips < teeth < jaw."""
        df = _make_declining_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_alligator("AAPL")
        assert result.lips_above_teeth is False
        assert result.teeth_above_jaw is False

    @patch("quantpilot_stock.alligator.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_alligator("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}

    @patch("quantpilot_stock.alligator.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_alligator("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.alligator.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_alligator("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.alligator.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_alligator("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"


# ---------------------------------------------------------------------------
# TestAlligatorAPI
# ---------------------------------------------------------------------------

class TestAlligatorAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/alligator")
        assert resp.status_code == 422

    @patch("quantpilot_stock.alligator.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/alligator?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.alligator.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/alligator?ticker=AAPL").json()
        for f in ["ticker", "jaw", "teeth", "lips", "lips_above_teeth",
                  "teeth_above_jaw", "price_above_jaw", "alligator_score",
                  "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.alligator.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/alligator?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
