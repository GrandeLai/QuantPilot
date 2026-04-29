"""Tests for Bollinger Band Squeeze — Phase F.38.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.bollinger.engine import (
    _classify_signal,
    _compute_bb,
    _compute_bb_score,
    _compute_pct_b,
    compute_bollinger,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_price_df(n: int, start: float = 100.0, step: float = 0.5) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    prices = [start + i * step for i in range(n)]
    return pd.DataFrame({"Close": prices}, index=idx)


def _make_flat_df(n: int, price: float = 100.0) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    return pd.DataFrame({"Close": [price] * n}, index=idx)


def _make_declining_df(n: int, start: float = 150.0, step: float = 0.5) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    prices = [start - i * step for i in range(n)]
    return pd.DataFrame({"Close": prices}, index=idx)


def _mock_ticker(df: pd.DataFrame) -> MagicMock:
    tk = MagicMock()
    tk.history.return_value = df
    return tk


# ---------------------------------------------------------------------------
# TestComputeBB
# ---------------------------------------------------------------------------

class TestComputeBB:
    def test_returns_five_values(self):
        df = _make_price_df(100)
        price, middle, upper, lower, bandwidth = _compute_bb(df["Close"])
        assert all(v is not None for v in [price, middle, upper, lower, bandwidth])

    def test_upper_greater_than_middle(self):
        df = _make_price_df(100)
        _, middle, upper, lower, _ = _compute_bb(df["Close"])
        assert upper > middle
        assert middle > lower

    def test_bandwidth_positive(self):
        df = _make_price_df(100)
        _, _, _, _, bandwidth = _compute_bb(df["Close"])
        assert bandwidth > 0

    def test_flat_price_narrow_bands(self):
        df = _make_flat_df(100)
        _, _, upper, lower, bandwidth = _compute_bb(df["Close"])
        # Flat price → std ≈ 0 → very narrow bands
        assert bandwidth < 0.01


# ---------------------------------------------------------------------------
# TestComputePctB
# ---------------------------------------------------------------------------

class TestComputePctB:
    def test_price_at_middle(self):
        # price = 100, upper = 110, lower = 90 → %B = 0.5
        pct = _compute_pct_b(100.0, 110.0, 90.0)
        assert abs(pct - 0.5) < 1e-9

    def test_price_at_upper(self):
        pct = _compute_pct_b(110.0, 110.0, 90.0)
        assert abs(pct - 1.0) < 1e-9

    def test_price_at_lower(self):
        pct = _compute_pct_b(90.0, 110.0, 90.0)
        assert abs(pct - 0.0) < 1e-9

    def test_price_above_upper(self):
        pct = _compute_pct_b(115.0, 110.0, 90.0)
        assert pct > 1.0

    def test_zero_bandwidth_returns_none(self):
        pct = _compute_pct_b(100.0, 100.0, 100.0)
        assert pct is None


# ---------------------------------------------------------------------------
# TestComputeBBScore
# ---------------------------------------------------------------------------

class TestComputeBBScore:
    def test_price_near_upper_bull_score(self):
        score = _compute_bb_score(pct_b=0.95, bandwidth_percentile=50)
        assert score >= 80.0

    def test_price_near_lower_bear_score(self):
        score = _compute_bb_score(pct_b=0.05, bandwidth_percentile=50)
        assert score <= 20.0

    def test_score_in_range(self):
        for pct_b in [0.1, 0.3, 0.5, 0.7, 0.9]:
            score = _compute_bb_score(pct_b=pct_b, bandwidth_percentile=50)
            assert 0.0 <= score <= 100.0

    def test_high_bw_percentile_bull_adds_score(self):
        score_low_bw = _compute_bb_score(pct_b=0.7, bandwidth_percentile=10)
        score_high_bw = _compute_bb_score(pct_b=0.7, bandwidth_percentile=80)
        assert score_high_bw > score_low_bw

    def test_none_pct_b_returns_midpoint(self):
        score = _compute_bb_score(pct_b=None, bandwidth_percentile=50)
        assert 40.0 <= score <= 60.0


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

    def test_boundary_80_is_strong_bull(self):
        assert _classify_signal(80.0) == "strong_bull"

    def test_boundary_60_is_bull(self):
        assert _classify_signal(60.0) == "bull"

    def test_boundary_40_is_neutral(self):
        assert _classify_signal(40.0) == "neutral"

    def test_boundary_20_is_bear(self):
        assert _classify_signal(20.0) == "bear"


# ---------------------------------------------------------------------------
# TestComputeBollingerIntegration
# ---------------------------------------------------------------------------

class TestComputeBollingerIntegration:
    @patch("quantpilot_stock.bollinger.engine.yf.Ticker")
    def test_data_available_with_adequate_data(self, mock_yf):
        df = _make_price_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_bollinger("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.bollinger.engine.yf.Ticker")
    def test_all_fields_populated(self, mock_yf):
        df = _make_price_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_bollinger("AAPL")
        assert result.middle is not None
        assert result.upper is not None
        assert result.lower is not None
        assert result.pct_b is not None
        assert result.bandwidth is not None

    @patch("quantpilot_stock.bollinger.engine.yf.Ticker")
    def test_rising_stock_bull_score(self, mock_yf):
        df = _make_price_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_bollinger("AAPL")
        assert result.bb_score > 50.0

    @patch("quantpilot_stock.bollinger.engine.yf.Ticker")
    def test_declining_stock_bear_score(self, mock_yf):
        df = _make_declining_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_bollinger("AAPL")
        assert result.bb_score < 50.0

    @patch("quantpilot_stock.bollinger.engine.yf.Ticker")
    def test_flat_stock_squeeze_active(self, mock_yf):
        # Flat price → very narrow BW → squeeze
        df = _make_flat_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_bollinger("AAPL")
        assert result.squeeze_active is True

    @patch("quantpilot_stock.bollinger.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_price_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_bollinger("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.bollinger.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_price_df(15)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_bollinger("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.bollinger.engine.yf.Ticker")
    def test_yfinance_exception_data_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_bollinger("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.bollinger.engine.yf.Ticker")
    def test_score_bounds(self, mock_yf):
        for df in [_make_price_df(200, step=2.0), _make_declining_df(200, step=2.0)]:
            mock_yf.return_value = _mock_ticker(df)
            result = compute_bollinger("AAPL")
            assert 0.0 <= result.bb_score <= 100.0

    @patch("quantpilot_stock.bollinger.engine.yf.Ticker")
    def test_upper_greater_than_lower(self, mock_yf):
        df = _make_price_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_bollinger("AAPL")
        assert result.upper is not None and result.lower is not None
        assert result.upper > result.lower


# ---------------------------------------------------------------------------
# TestBollingerAPI
# ---------------------------------------------------------------------------

class TestBollingerAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/bollinger")
        assert resp.status_code == 422

    @patch("quantpilot_stock.bollinger.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_price_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/bollinger?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.bollinger.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_price_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/bollinger?ticker=AAPL").json()
        for f in ["ticker", "middle", "upper", "lower", "pct_b",
                  "bandwidth", "squeeze_active", "bb_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.bollinger.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/bollinger?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
