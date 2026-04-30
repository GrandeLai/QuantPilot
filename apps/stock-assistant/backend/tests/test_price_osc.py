"""Tests for Price Oscillator (PO) — Phase F.73.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.price_osc.engine import (
    _classify_signal,
    _compute_po_score,
    _compute_po_series,
    compute_po,
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
            "High":   [c + 1.0 for c in closes],
            "Low":    [c - 1.0 for c in closes],
            "Close":  closes,
            "Volume": [1_000_000] * n,
        },
        index=idx,
    )


def _make_declining_df(n: int, start: float = 200.0, step: float = 0.5) -> pd.DataFrame:
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
# TestComputePOSeries
# ---------------------------------------------------------------------------

class TestComputePOSeries:
    def test_returns_two_series(self):
        df = _make_ohlcv_df(200)
        result = _compute_po_series(df["Close"])
        assert len(result) == 2

    def test_lengths_match_input(self):
        df = _make_ohlcv_df(200)
        po, sig = _compute_po_series(df["Close"])
        assert len(po) == len(sig) == 200

    def test_rising_price_positive_po(self):
        """Rising prices → SMA(fast) > SMA(slow) → PO > 0."""
        df = _make_ohlcv_df(200, step=1.0)
        po, _ = _compute_po_series(df["Close"])
        assert float(po.iloc[-1]) > 0.0

    def test_declining_price_negative_po(self):
        """Declining prices → SMA(fast) < SMA(slow) → PO < 0."""
        df = _make_declining_df(200, step=1.0)
        po, _ = _compute_po_series(df["Close"])
        assert float(po.iloc[-1]) < 0.0

    def test_flat_price_near_zero(self):
        """Flat prices → SMA(fast) ≈ SMA(slow) → PO ≈ 0."""
        df = _make_ohlcv_df(200, step=0.0)
        po, _ = _compute_po_series(df["Close"])
        assert abs(float(po.iloc[-1])) < 0.1

    def test_no_nan_at_end(self):
        df = _make_ohlcv_df(200)
        po, sig = _compute_po_series(df["Close"])
        assert po.iloc[-1] == po.iloc[-1]
        assert sig.iloc[-1] == sig.iloc[-1]

    def test_no_inf_values(self):
        import math
        df = _make_ohlcv_df(200)
        po, sig = _compute_po_series(df["Close"])
        for s in (po, sig):
            assert all(math.isfinite(v) for v in s.dropna())

    def test_custom_periods(self):
        df = _make_ohlcv_df(200)
        po5_20, _ = _compute_po_series(df["Close"], fast=5, slow=20, signal=9)
        po10_30, _ = _compute_po_series(df["Close"], fast=10, slow=30, signal=9)
        assert len(po5_20) == len(po10_30) == 200


# ---------------------------------------------------------------------------
# TestComputePOScore
# ---------------------------------------------------------------------------

class TestComputePOScore:
    def _make_series(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_po_above_signal_and_positive(self):
        series = self._make_series([float(i) for i in range(-50, 51)])
        score = _compute_po_score(5.0, 2.0, series)
        assert score >= 70.0

    def test_po_below_signal_and_negative(self):
        series = self._make_series([float(i) for i in range(-50, 0)])
        score = _compute_po_score(-5.0, -2.0, series)
        assert score < 40.0

    def test_score_in_range(self):
        series = self._make_series([0.0] * 100)
        for po, sig in [(3.0, 1.0), (-3.0, -1.0), (0.0, 0.0)]:
            score = _compute_po_score(po, sig, series)
            assert 0.0 <= score <= 100.0

    def test_short_series_fallback(self):
        series = self._make_series([1.0, 2.0, 3.0])
        score = _compute_po_score(2.0, 1.0, series)
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
# TestComputePOIntegration
# ---------------------------------------------------------------------------

class TestComputePOIntegration:
    @patch("quantpilot_stock.price_osc.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_po("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.price_osc.engine.yf.Ticker")
    def test_fields_populated(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_po("AAPL")
        assert result.po_value is not None
        assert result.signal_value is not None
        assert isinstance(result.po_above_signal, bool)
        assert isinstance(result.po_positive, bool)

    @patch("quantpilot_stock.price_osc.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_po("AAPL")
        assert 0.0 <= result.po_score <= 100.0

    @patch("quantpilot_stock.price_osc.engine.yf.Ticker")
    def test_rising_stock_positive_po(self, mock_yf):
        df = _make_ohlcv_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_po("AAPL")
        assert result.po_positive is True

    @patch("quantpilot_stock.price_osc.engine.yf.Ticker")
    def test_declining_stock_negative_po(self, mock_yf):
        df = _make_declining_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_po("AAPL")
        assert result.po_positive is False

    @patch("quantpilot_stock.price_osc.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_po("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.price_osc.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_po("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}

    @patch("quantpilot_stock.price_osc.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(10)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_po("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.price_osc.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_po("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"


# ---------------------------------------------------------------------------
# TestPriceOscAPI
# ---------------------------------------------------------------------------

class TestPriceOscAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/price_osc")
        assert resp.status_code == 422

    @patch("quantpilot_stock.price_osc.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/price_osc?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.price_osc.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/price_osc?ticker=AAPL").json()
        for f in ["ticker", "po_value", "signal_value", "po_above_signal",
                  "po_positive", "po_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.price_osc.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/price_osc?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
