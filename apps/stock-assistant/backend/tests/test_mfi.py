"""Tests for Money Flow Index — Phase F.42.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.mfi.engine import (
    _classify_signal,
    _compute_mfi_score,
    _compute_mfi_series,
    _detect_mfi_divergence,
    compute_mfi,
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
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [start + i * step for i in range(n)]
    return pd.DataFrame({
        "Open": closes,
        "High": [c + 1.0 for c in closes],
        "Low": [c - 1.0 for c in closes],
        "Close": closes,
        "Volume": [volume] * n,
    }, index=idx)


def _make_declining_ohlcv(n: int, start: float = 150.0, step: float = 0.5) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    closes = [start - i * step for i in range(n)]
    return pd.DataFrame({
        "Open": closes,
        "High": [c + 1.0 for c in closes],
        "Low": [c - 1.0 for c in closes],
        "Close": closes,
        "Volume": [1_000_000] * n,
    }, index=idx)


def _mock_ticker(df: pd.DataFrame) -> MagicMock:
    tk = MagicMock()
    tk.history.return_value = df
    return tk


# ---------------------------------------------------------------------------
# TestComputeMFISeries
# ---------------------------------------------------------------------------

class TestComputeMFISeries:
    def test_rising_stock_high_mfi(self):
        df = _make_ohlcv_df(100)
        mfi = _compute_mfi_series(df["High"], df["Low"], df["Close"], df["Volume"])
        # Consistently rising → typical price increases → positive money flow dominant
        assert float(mfi.iloc[-1]) > 50.0

    def test_declining_stock_low_mfi(self):
        df = _make_declining_ohlcv(100)
        mfi = _compute_mfi_series(df["High"], df["Low"], df["Close"], df["Volume"])
        assert float(mfi.iloc[-1]) < 50.0

    def test_mfi_length_matches_input(self):
        df = _make_ohlcv_df(100)
        mfi = _compute_mfi_series(df["High"], df["Low"], df["Close"], df["Volume"])
        assert len(mfi) == len(df)

    def test_mfi_in_range(self):
        df = _make_ohlcv_df(100)
        mfi = _compute_mfi_series(df["High"], df["Low"], df["Close"], df["Volume"])
        assert float(mfi.min()) >= 0.0
        assert float(mfi.max()) <= 100.0

    def test_alternating_volume_mfi_midpoint(self):
        """Alternating up/down days with equal volume → MFI near 50."""
        idx = pd.date_range("2022-01-01", periods=60, freq="B")
        closes = [100.0 + (1.0 if i % 2 == 0 else -1.0) for i in range(60)]
        df = pd.DataFrame({
            "High": [c + 0.5 for c in closes],
            "Low": [c - 0.5 for c in closes],
            "Close": closes,
            "Volume": [1_000_000] * 60,
        }, index=idx)
        mfi = _compute_mfi_series(df["High"], df["Low"], df["Close"], df["Volume"])
        # With exactly alternating, MFI should hover around 50
        assert 30.0 < float(mfi.iloc[-1]) < 70.0


# ---------------------------------------------------------------------------
# TestDetectMFIDivergence
# ---------------------------------------------------------------------------

class TestDetectMFIDivergence:
    def test_no_divergence_on_short_data(self):
        idx = pd.date_range("2022-01-01", periods=5, freq="B")
        c = pd.Series([100.0] * 5, index=idx)
        mfi = pd.Series([50.0] * 5, index=idx)
        bull, bear = _detect_mfi_divergence(c, mfi)
        assert bull is False
        assert bear is False

    def test_bullish_divergence_detected(self):
        """Price makes lower low in second half; MFI makes higher low."""
        idx = pd.date_range("2022-01-01", periods=20, freq="B")
        # First half: price 100-90, MFI 30-20
        # Second half: price 85-80 (lower low), MFI 35-40 (higher low)
        prices_first = [100.0 - i for i in range(10)]
        prices_second = [85.0 - 0.5 * i for i in range(10)]
        mfi_first = [30.0 - i for i in range(10)]
        mfi_second = [35.0 + i * 0.5 for i in range(10)]
        c = pd.Series(prices_first + prices_second, index=idx)
        m = pd.Series(mfi_first + mfi_second, index=idx)
        bull, bear = _detect_mfi_divergence(c, m, lookback=20)
        assert bull is True

    def test_bearish_divergence_detected(self):
        """Price makes higher high in second half; MFI makes lower high."""
        idx = pd.date_range("2022-01-01", periods=20, freq="B")
        prices_first = [100.0 + i for i in range(10)]
        prices_second = [115.0 + i for i in range(10)]   # higher high
        mfi_first = [70.0 + i for i in range(10)]
        mfi_second = [65.0 - i * 0.5 for i in range(10)]  # lower high
        c = pd.Series(prices_first + prices_second, index=idx)
        m = pd.Series(mfi_first + mfi_second, index=idx)
        bull, bear = _detect_mfi_divergence(c, m, lookback=20)
        assert bear is True


# ---------------------------------------------------------------------------
# TestComputeMFIScore
# ---------------------------------------------------------------------------

class TestComputeMFIScore:
    def test_high_mfi_high_score(self):
        score = _compute_mfi_score(85.0, False, False)
        assert score >= 80.0

    def test_low_mfi_low_score(self):
        score = _compute_mfi_score(15.0, False, False)
        assert score <= 20.0

    def test_bullish_divergence_boosts_score(self):
        base = _compute_mfi_score(50.0, False, False)
        boosted = _compute_mfi_score(50.0, True, False)
        assert boosted > base

    def test_bearish_divergence_lowers_score(self):
        base = _compute_mfi_score(50.0, False, False)
        lowered = _compute_mfi_score(50.0, False, True)
        assert lowered < base

    def test_score_clipped_to_range(self):
        assert _compute_mfi_score(98.0, True, False) <= 100.0
        assert _compute_mfi_score(2.0, False, True) >= 0.0


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
# TestComputeMFIIntegration
# ---------------------------------------------------------------------------

class TestComputeMFIIntegration:
    @patch("quantpilot_stock.mfi.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_mfi("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.mfi.engine.yf.Ticker")
    def test_mfi_populated(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_mfi("AAPL")
        assert result.mfi is not None
        assert 0.0 <= result.mfi <= 100.0

    @patch("quantpilot_stock.mfi.engine.yf.Ticker")
    def test_rising_stock_bull_score(self, mock_yf):
        df = _make_ohlcv_df(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_mfi("AAPL")
        assert result.mfi_score > 50.0

    @patch("quantpilot_stock.mfi.engine.yf.Ticker")
    def test_declining_stock_bear_score(self, mock_yf):
        df = _make_declining_ohlcv(200, step=1.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_mfi("AAPL")
        assert result.mfi_score < 50.0

    @patch("quantpilot_stock.mfi.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_mfi("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.mfi.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(15)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_mfi("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.mfi.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_mfi("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"

    @patch("quantpilot_stock.mfi.engine.yf.Ticker")
    def test_score_bounds(self, mock_yf):
        for df in [_make_ohlcv_df(200, step=3.0), _make_declining_ohlcv(200, step=3.0)]:
            mock_yf.return_value = _mock_ticker(df)
            result = compute_mfi("AAPL")
            assert 0.0 <= result.mfi_score <= 100.0

    @patch("quantpilot_stock.mfi.engine.yf.Ticker")
    def test_overbought_flag(self, mock_yf):
        """Strongly rising stock should trigger overbought."""
        df = _make_ohlcv_df(200, step=2.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_mfi("AAPL")
        # MFI should be >= 80 for a strongly rising stock
        assert result.overbought is True

    @patch("quantpilot_stock.mfi.engine.yf.Ticker")
    def test_oversold_flag(self, mock_yf):
        """Strongly declining stock should trigger oversold."""
        df = _make_declining_ohlcv(200, step=2.0)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_mfi("AAPL")
        assert result.oversold is True

    @patch("quantpilot_stock.mfi.engine.yf.Ticker")
    def test_direction_populated(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_mfi("AAPL")
        assert result.mfi_direction in ("rising", "falling", "flat")


# ---------------------------------------------------------------------------
# TestMFIAPI
# ---------------------------------------------------------------------------

class TestMFIAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/mfi")
        assert resp.status_code == 422

    @patch("quantpilot_stock.mfi.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/mfi?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.mfi.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/mfi?ticker=AAPL").json()
        for f in ["ticker", "mfi", "overbought", "oversold", "bullish_divergence",
                  "bearish_divergence", "mfi_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.mfi.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/mfi?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
