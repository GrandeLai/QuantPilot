"""Tests for Connors RSI (CRSI) — F.81.

All network calls are mocked. Target ≥ 16 tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from quantpilot_stock.connors_rsi.engine import (
    _classify_signal,
    _compute_crsi_score,
    _compute_crsi_series,
    _compute_percent_rank,
    _compute_rsi,
    _compute_streak,
    compute_crsi,
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


def _make_close(vals: list[float]) -> pd.Series:
    idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
    return pd.Series(vals, index=idx)


# ---------------------------------------------------------------------------
# TestComputeStreak
# ---------------------------------------------------------------------------

class TestComputeStreak:
    def test_all_up_days_positive_streak(self):
        close = _make_close([100.0, 101.0, 102.0, 103.0, 104.0])
        streak = _compute_streak(close)
        assert float(streak.iloc[-1]) == 4.0

    def test_all_down_days_negative_streak(self):
        close = _make_close([104.0, 103.0, 102.0, 101.0, 100.0])
        streak = _compute_streak(close)
        assert float(streak.iloc[-1]) == -4.0

    def test_streak_resets_on_reversal(self):
        close = _make_close([100.0, 101.0, 102.0, 101.0])
        streak = _compute_streak(close)
        assert float(streak.iloc[-1]) == -1.0

    def test_flat_day_resets_streak(self):
        close = _make_close([100.0, 101.0, 101.0, 102.0])
        streak = _compute_streak(close)
        assert float(streak.iloc[-1]) == 1.0

    def test_length_preserved(self):
        close = _make_close([float(i) for i in range(50)])
        streak = _compute_streak(close)
        assert len(streak) == 50


# ---------------------------------------------------------------------------
# TestComputeRSI
# ---------------------------------------------------------------------------

class TestComputeRSI:
    def test_all_up_returns_near_100(self):
        close = _make_close([100.0 + i for i in range(50)])
        rsi = _compute_rsi(close, 3)
        assert float(rsi.iloc[-1]) > 90.0

    def test_all_down_returns_near_0(self):
        close = _make_close([100.0 - i for i in range(50)])
        rsi = _compute_rsi(close, 3)
        assert float(rsi.iloc[-1]) < 10.0

    def test_range_0_to_100(self):
        close = _make_close([100.0 + i * 0.1 for i in range(200)])
        rsi = _compute_rsi(close, 14)
        assert rsi.min() >= 0.0
        assert rsi.max() <= 100.0


# ---------------------------------------------------------------------------
# TestComputePercentRank
# ---------------------------------------------------------------------------

class TestComputePercentRank:
    def test_range_0_to_100(self):
        roc = _make_close([0.01 * i for i in range(200)])
        prank = _compute_percent_rank(roc, 100)
        assert prank.dropna().min() >= 0.0
        assert prank.dropna().max() <= 100.0

    def test_length_preserved(self):
        roc = _make_close([0.01 * i for i in range(200)])
        prank = _compute_percent_rank(roc, 100)
        assert len(prank) == 200


# ---------------------------------------------------------------------------
# TestComputeCRSISeries
# ---------------------------------------------------------------------------

class TestComputeCRSISeries:
    def test_returns_four_series(self):
        close = _make_close([100.0 + i * 0.5 for i in range(200)])
        crsi, rsi3, srsi, prank = _compute_crsi_series(close)
        for s in [crsi, rsi3, srsi, prank]:
            assert isinstance(s, pd.Series)

    def test_crsi_in_range(self):
        close = _make_close([100.0 + i * 0.5 for i in range(200)])
        crsi, _, _, _ = _compute_crsi_series(close)
        assert crsi.min() >= 0.0
        assert crsi.max() <= 100.0

    def test_all_rising_crsi_above_50(self):
        """All-up days → RSI(3) high, streak RSI high, prank high → CRSI > 50."""
        close = _make_close([100.0 + i for i in range(200)])
        crsi, _, _, _ = _compute_crsi_series(close)
        assert float(crsi.iloc[-1]) > 50.0

    def test_all_declining_crsi_below_50(self):
        """All-down days → RSI(3) low, streak RSI low → CRSI < 50."""
        close = _make_close([200.0 - i for i in range(200)])
        crsi, _, _, _ = _compute_crsi_series(close)
        assert float(crsi.iloc[-1]) < 50.0


# ---------------------------------------------------------------------------
# TestComputeCRSIScore
# ---------------------------------------------------------------------------

class TestComputeCRSIScore:
    def _make_crsi(self, vals: list[float]) -> pd.Series:
        idx = pd.date_range("2022-01-01", periods=len(vals), freq="B")
        return pd.Series(vals, index=idx)

    def test_rising_crsi_above_50_scores_high(self):
        crsi = self._make_crsi([55.0 + i * 0.1 for i in range(252)])
        score = _compute_crsi_score(crsi)
        assert score >= 60.0

    def test_falling_crsi_below_50_scores_low(self):
        crsi = self._make_crsi([45.0 - i * 0.1 for i in range(252)])
        score = _compute_crsi_score(crsi)
        assert score < 40.0

    def test_score_in_range(self):
        crsi = self._make_crsi([50.0] * 252)
        score = _compute_crsi_score(crsi)
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
# TestComputeCRSIIntegration
# ---------------------------------------------------------------------------

class TestComputeCRSIIntegration:
    @patch("quantpilot_stock.connors_rsi.engine.yf.Ticker")
    def test_data_available(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_crsi("AAPL")
        assert result.data_available is True

    @patch("quantpilot_stock.connors_rsi.engine.yf.Ticker")
    def test_fields_populated(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_crsi("AAPL")
        assert result.crsi_value is not None
        assert result.rsi3 is not None
        assert result.streak_rsi is not None
        assert result.percent_rank is not None

    @patch("quantpilot_stock.connors_rsi.engine.yf.Ticker")
    def test_score_in_range(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_crsi("AAPL")
        assert 0.0 <= result.crsi_score <= 100.0

    @patch("quantpilot_stock.connors_rsi.engine.yf.Ticker")
    def test_crsi_in_range(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_crsi("AAPL")
        assert 0.0 <= (result.crsi_value or 0.0) <= 100.0

    @patch("quantpilot_stock.connors_rsi.engine.yf.Ticker")
    def test_signal_valid_enum(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_crsi("AAPL")
        assert result.signal in {"strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"}

    @patch("quantpilot_stock.connors_rsi.engine.yf.Ticker")
    def test_interpretation_nonempty(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_crsi("AAPL")
        assert len(result.interpretation) > 10

    @patch("quantpilot_stock.connors_rsi.engine.yf.Ticker")
    def test_insufficient_data_graceful(self, mock_yf):
        df = _make_ohlcv_df(50)
        mock_yf.return_value = _mock_ticker(df)
        result = compute_crsi("AAPL")
        assert result.data_available is True
        assert result.signal == "no_data"

    @patch("quantpilot_stock.connors_rsi.engine.yf.Ticker")
    def test_yfinance_exception_unavailable(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        result = compute_crsi("AAPL")
        assert result.data_available is False
        assert result.signal == "no_data"


# ---------------------------------------------------------------------------
# TestConnorsRSIAPI
# ---------------------------------------------------------------------------

class TestConnorsRSIAPI:
    def _get_client(self):
        from fastapi.testclient import TestClient
        from quantpilot_stock.main import create_app
        return TestClient(create_app())

    def test_no_ticker_returns_422(self):
        client = self._get_client()
        resp = client.get("/api/connors_rsi")
        assert resp.status_code == 422

    @patch("quantpilot_stock.connors_rsi.engine.yf.Ticker")
    def test_with_ticker_returns_200(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        resp = client.get("/api/connors_rsi?ticker=AAPL")
        assert resp.status_code == 200

    @patch("quantpilot_stock.connors_rsi.engine.yf.Ticker")
    def test_response_has_required_fields(self, mock_yf):
        df = _make_ohlcv_df(200)
        mock_yf.return_value = _mock_ticker(df)
        client = self._get_client()
        body = client.get("/api/connors_rsi?ticker=AAPL").json()
        for f in ["ticker", "crsi_value", "rsi3", "streak_rsi", "percent_rank",
                  "crsi_score", "signal", "data_available"]:
            assert f in body

    @patch("quantpilot_stock.connors_rsi.engine.yf.Ticker")
    def test_yfinance_fail_still_200(self, mock_yf):
        mock_yf.side_effect = RuntimeError("network error")
        client = self._get_client()
        resp = client.get("/api/connors_rsi?ticker=AAPL")
        assert resp.status_code == 200
        assert resp.json()["data_available"] is False
