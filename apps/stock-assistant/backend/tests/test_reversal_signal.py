"""Tests for Short-Term Reversal Signal — Phase F.34.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from quantpilot_stock.reversal_signal.engine import (
    _classify_signal,
    _compute_reversal_score,
    compute_reversal,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_price_df(n: int, start: float = 100.0, step: float = 0.5) -> pd.DataFrame:
    idx = pd.date_range("2023-01-01", periods=n, freq="B")
    prices = [start + i * step for i in range(n)]
    volumes = [1_000_000] * n
    return pd.DataFrame({"Close": prices, "Volume": volumes}, index=idx)


def _mock_side_effect(
    stock_df: pd.DataFrame,
    spy_df: pd.DataFrame,
) -> Callable[[str], MagicMock]:
    def _inner(symbol: str) -> MagicMock:
        tk = MagicMock()
        tk.history.return_value = spy_df if symbol == "SPY" else stock_df
        return tk
    return _inner


# ---------------------------------------------------------------------------
# TestComputeReversalScore
# ---------------------------------------------------------------------------

class TestComputeReversalScore:
    def test_heavily_underperformed_strong_positive(self):
        """rel_1w = -8%, rel_4w = -12% → strong long reversal signal."""
        score = _compute_reversal_score(-0.08, -0.12, None)
        assert score >= 60.0

    def test_heavily_outperformed_strong_negative(self):
        """rel_1w = +8%, rel_4w = +12% → strong short reversal signal."""
        score = _compute_reversal_score(0.08, 0.12, None)
        assert score <= -60.0

    def test_neutral_near_zero(self):
        """rel_1w ≈ 0, rel_4w ≈ 0 → near zero score."""
        score = _compute_reversal_score(0.0, 0.0, None)
        assert abs(score) < 5.0

    def test_score_clipped_at_100(self):
        score = _compute_reversal_score(-0.5, -0.5, None)
        assert score <= 100.0

    def test_score_clipped_at_minus_100(self):
        score = _compute_reversal_score(0.5, 0.5, None)
        assert score >= -100.0

    def test_low_volume_boosts_long_reversal(self):
        """vol_ratio < 0.7 with negative rel_1w adds +20 to score."""
        score_without_vol = _compute_reversal_score(-0.03, -0.06, None)
        score_with_low_vol = _compute_reversal_score(-0.03, -0.06, 0.5)
        assert score_with_low_vol > score_without_vol

    def test_low_volume_reduces_short_reversal(self):
        """vol_ratio < 0.7 with positive rel_1w subtracts 20."""
        score_without_vol = _compute_reversal_score(0.03, 0.06, None)
        score_with_low_vol = _compute_reversal_score(0.03, 0.06, 0.5)
        assert score_with_low_vol < score_without_vol


# ---------------------------------------------------------------------------
# TestClassifySignal
# ---------------------------------------------------------------------------

class TestClassifySignal:
    def test_strong_reversal_up(self):
        assert _classify_signal(70.0) == "strong_reversal_up"

    def test_reversal_up(self):
        assert _classify_signal(40.0) == "reversal_up"

    def test_neutral(self):
        assert _classify_signal(0.0) == "neutral"

    def test_reversal_down(self):
        assert _classify_signal(-40.0) == "reversal_down"

    def test_strong_reversal_down(self):
        assert _classify_signal(-70.0) == "strong_reversal_down"

    def test_none_returns_no_data(self):
        assert _classify_signal(None) == "no_data"

    def test_boundary_60_is_strong_up(self):
        assert _classify_signal(60.0) == "strong_reversal_up"

    def test_boundary_30_is_reversal_up(self):
        assert _classify_signal(30.0) == "reversal_up"

    def test_boundary_minus_30_is_neutral(self):
        assert _classify_signal(-29.9) == "neutral"

    def test_boundary_minus_60_is_strong_down(self):
        # -60 is NOT > -60, so falls to strong_reversal_down
        assert _classify_signal(-60.0) == "strong_reversal_down"


# ---------------------------------------------------------------------------
# TestComputeReversalIntegration
# ---------------------------------------------------------------------------

class TestComputeReversalIntegration:
    @patch("quantpilot_stock.reversal_signal.engine.yf.Ticker")
    def test_data_available_true(self, mock_yf):
        df = _make_price_df(100)
        mock_yf.side_effect = _mock_side_effect(df, df)
        result = compute_reversal("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.reversal_signal.engine.yf.Ticker")
    def test_fields_populated(self, mock_yf):
        df = _make_price_df(100)
        mock_yf.side_effect = _mock_side_effect(df, df)
        result = compute_reversal("AAPL")
        assert result.rel_1w is not None
        assert result.rel_4w is not None

    @patch("quantpilot_stock.reversal_signal.engine.yf.Ticker")
    def test_equal_performance_neutral(self, mock_yf):
        """Same stock and SPY → rel = 0, neutral or close to neutral."""
        df = _make_price_df(100)
        mock_yf.side_effect = _mock_side_effect(df, df)
        result = compute_reversal("AAPL")
        assert result.rel_1w == pytest.approx(0.0, abs=1e-9)
        assert result.signal == "neutral"

    @patch("quantpilot_stock.reversal_signal.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_price_df(100)
        mock_yf.side_effect = _mock_side_effect(df, df)
        result = compute_reversal("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.reversal_signal.engine.yf.Ticker")
    def test_underperforming_stock_positive_score(self, mock_yf):
        """Flat stock vs rising SPY → positive reversal score."""
        stock_df = _make_price_df(100, step=0.0)
        spy_df = _make_price_df(100, step=1.0)
        mock_yf.side_effect = _mock_side_effect(stock_df, spy_df)
        result = compute_reversal("AAPL")
        assert result.reversal_score > 0

    @patch("quantpilot_stock.reversal_signal.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_price_df(10)
        mock_yf.side_effect = _mock_side_effect(df, df)
        result = compute_reversal("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.reversal_signal.engine.yf.Ticker")
    def test_yfinance_exception_data_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_reversal("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.reversal_signal.engine.yf.Ticker")
    def test_vol_ratio_populated(self, mock_yf):
        df = _make_price_df(100)
        mock_yf.side_effect = _mock_side_effect(df, df)
        result = compute_reversal("AAPL")
        assert result.vol_ratio is not None


# ---------------------------------------------------------------------------
# TestReversalSignalAPI
# ---------------------------------------------------------------------------

class TestReversalSignalAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/reversal-signal")
        assert resp.status_code == 422

    @patch("quantpilot_stock.reversal_signal.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_price_df(100)
        mock_yf.side_effect = _mock_side_effect(df, df)
        client = self._get_client()
        resp = client.get("/api/reversal-signal?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.reversal_signal.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_price_df(100)
        mock_yf.side_effect = _mock_side_effect(df, df)
        client = self._get_client()
        body = client.get("/api/reversal-signal?ticker=AAPL").json()
        for f in ["ticker", "rel_1w", "rel_4w", "reversal_score", "signal", "data_available", "interpretation"]:
            assert f in body

    @patch("quantpilot_stock.reversal_signal.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/reversal-signal?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
