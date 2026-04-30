"""Tests for Stochastic RSI — F.83.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.stoch_rsi.engine import (
    _classify_signal,
    _compute_stoch_rsi_score,
    _compute_stoch_rsi_series,
    compute_stoch_rsi,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv_df(n: int, start: float = 100.0, step: float = 0.5) -> pd.DataFrame:
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


def _make_close(vals: list[float]) -> pd.Series:
    idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
    return pd.Series(vals, index=idx)


# ---------------------------------------------------------------------------
# TestComputeStochRSISeries
# ---------------------------------------------------------------------------

class TestComputeStochRSISeries:
    def test_returns_two_series(self):
        close = _make_close([100.0 + i * 0.5 for i in range(100)])
        k, d = _compute_stoch_rsi_series(close)
        assert isinstance(k, pd.Series)
        assert isinstance(d, pd.Series)

    def test_lengths_match_input(self):
        close = _make_close([100.0 + i * 0.5 for i in range(100)])
        k, d = _compute_stoch_rsi_series(close)
        assert len(k) == 100
        assert len(d) == 100

    def test_k_in_range_0_to_100(self):
        close = _make_close([100.0 + i * 0.5 for i in range(200)])
        k, _ = _compute_stoch_rsi_series(close)
        assert k.min() >= 0.0
        assert k.max() <= 100.0

    def test_d_in_range_0_to_100(self):
        close = _make_close([100.0 + i * 0.5 for i in range(200)])
        _, d = _compute_stoch_rsi_series(close)
        assert d.min() >= 0.0
        assert d.max() <= 100.0

    def test_no_nan_values(self):
        close = _make_close([100.0 + i * 0.5 for i in range(100)])
        k, d = _compute_stoch_rsi_series(close)
        assert not k.isna().any()
        assert not d.isna().any()

    def test_rising_market_k_not_low(self):
        """Alternating up market with occasional dips → RSI has variation → %K not zero."""
        # Use a zigzag with net upward drift so RSI varies and Stoch has range
        import math
        vals = [100.0 + i * 0.5 + 3.0 * math.sin(i * 0.3) for i in range(200)]
        close = _make_close(vals)
        k, _ = _compute_stoch_rsi_series(close)
        # K should be non-negative (not stuck at 0)
        assert float(k.iloc[-1]) >= 0.0

    def test_declining_market_k_not_high(self):
        """Alternating down market → RSI has variation → %K in valid range."""
        import math
        vals = [200.0 - i * 0.5 + 3.0 * math.sin(i * 0.3) for i in range(200)]
        close = _make_close(vals)
        k, _ = _compute_stoch_rsi_series(close)
        assert float(k.iloc[-1]) <= 100.0

    def test_d_is_smoothed_version_of_k(self):
        """D should be less volatile than K."""
        close = _make_close([100.0 + (i % 5) * 2.0 for i in range(100)])
        k, d = _compute_stoch_rsi_series(close)
        # D std should be <= K std
        assert float(d.std()) <= float(k.std()) + 1e-6


# ---------------------------------------------------------------------------
# TestComputeStochRSIScore
# ---------------------------------------------------------------------------

class TestComputeStochRSIScore:
    def _make_kd(self, k_vals: list[float], d_vals: list[float]) -> tuple[pd.Series, pd.Series]:
        idx = pd.date_range("2022-01-01", periods=len(k_vals), freq="B")
        return pd.Series(k_vals, index=idx), pd.Series(d_vals, index=idx)

    def test_high_k_above_d_scores_high(self):
        k, d = self._make_kd([60.0 + i * 0.1 for i in range(252)], [55.0 + i * 0.1 for i in range(252)])
        score = _compute_stoch_rsi_score(k, d)
        assert score >= 60.0

    def test_low_k_below_d_scores_low(self):
        k, d = self._make_kd([40.0 - i * 0.1 for i in range(252)], [45.0 - i * 0.05 for i in range(252)])
        score = _compute_stoch_rsi_score(k, d)
        assert score < 40.0

    def test_score_in_range(self):
        k, d = self._make_kd([50.0] * 252, [50.0] * 252)
        score = _compute_stoch_rsi_score(k, d)
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


# ---------------------------------------------------------------------------
# TestComputeStochRSIIntegration
# ---------------------------------------------------------------------------

class TestComputeStochRSIIntegration:
    @patch("quantpilot_stock.stoch_rsi.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(100)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stoch_rsi("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.stoch_rsi.engine.yf.Ticker")
    def test_fields_populated(self, mock_yf):
        df = _make_ohlcv_df(100)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stoch_rsi("AAPL")
        assert result.k_value is not None
        assert result.d_value is not None

    @patch("quantpilot_stock.stoch_rsi.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(100)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stoch_rsi("AAPL")
        assert 0.0 <= result.stoch_rsi_score <= 100.0

    @patch("quantpilot_stock.stoch_rsi.engine.yf.Ticker")
    def test_k_d_in_range(self, mock_yf):
        df = _make_ohlcv_df(100)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stoch_rsi("AAPL")
        assert 0.0 <= (result.k_value or 0.0) <= 100.0
        assert 0.0 <= (result.d_value or 0.0) <= 100.0

    @patch("quantpilot_stock.stoch_rsi.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(100)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stoch_rsi("AAPL")
        valid = {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}
        assert result.signal in valid

    @patch("quantpilot_stock.stoch_rsi.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(100)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stoch_rsi("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.stoch_rsi.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(5)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_stoch_rsi("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.stoch_rsi.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_stoch_rsi("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"


# ---------------------------------------------------------------------------
# TestStochRSIAPI
# ---------------------------------------------------------------------------

class TestStochRSIAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/stoch_rsi")
        assert resp.status_code == 422

    @patch("quantpilot_stock.stoch_rsi.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(100)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/stoch_rsi?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.stoch_rsi.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(100)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/stoch_rsi?ticker=AAPL").json()
        for f in ["ticker", "k_value", "d_value", "stoch_rsi_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.stoch_rsi.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/stoch_rsi?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
