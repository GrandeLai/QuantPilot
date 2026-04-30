"""Price Oscillator (PO) engine — Phase F.73.

PO Formula:
  PO      = (SMA(fast, close) − SMA(slow, close)) / SMA(slow, close) × 100
  Signal  = SMA(signal_period, PO)

  Defaults: fast=10, slow=21, signal=9

Score (0–100):
  40 pts  PO > Signal
  30 pts  PO > 0
  30 pts  percentile rank of PO in 252-bar window × 30

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

POSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_FAST_PERIOD   = 10
_SLOW_PERIOD   = 21
_SIGNAL_PERIOD = 9
_MIN_BARS      = _SLOW_PERIOD + _SIGNAL_PERIOD + 5


@dataclass
class POData:
    ticker: str
    po_value: float | None = None
    signal_value: float | None = None
    po_above_signal: bool | None = None
    po_positive: bool | None = None
    po_score: float = 50.0
    signal: POSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_po_series(
    close: pd.Series,
    fast: int = _FAST_PERIOD,
    slow: int = _SLOW_PERIOD,
    signal: int = _SIGNAL_PERIOD,
) -> tuple[pd.Series, pd.Series]:
    """Return (po, signal_line) series."""
    sma_fast = close.rolling(fast).mean()
    sma_slow = close.rolling(slow).mean()
    po       = ((sma_fast - sma_slow) / sma_slow.replace(0, float("nan")) * 100).fillna(0.0)
    sig      = po.rolling(signal).mean().fillna(po)
    return po, sig


def _compute_po_score(
    po_val: float,
    sig_val: float,
    po_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Composite score 0–100."""
    above_pts = 40.0 if po_val > sig_val else 0.0
    pos_pts   = 30.0 if po_val > 0 else 0.0

    window = po_series.dropna().iloc[-lookback:]
    if len(window) < 10:
        pct_pts = 15.0
    else:
        pct_pts = float((window < po_val).mean()) * 30.0

    return round(above_pts + pos_pts + pct_pts, 1)


def _classify_signal(score: float | None) -> POSignal:
    if score is None:
        return "no_data"
    if score >= 80:
        return "strong_bull"
    if score >= 60:
        return "bull"
    if score >= 40:
        return "neutral"
    if score >= 20:
        return "bear"
    return "strong_bear"


def _build_interpretation(
    ticker: str,
    signal: POSignal,
    po_val: float,
    above: bool,
    positive: bool,
    score: float,
) -> str:
    above_str = "高于信号线" if above else "低于信号线"
    pos_str   = "正值(均线多头排列)" if positive else "负值(均线空头排列)"
    labels: dict[POSignal, str] = {
        "strong_bull": (
            f"{ticker} PO={po_val:.2f}%，{above_str}，{pos_str}（得分 {score:.0f}）：价格振荡动能极强，短均线大幅领先长均线。"
        ),
        "bull": (
            f"{ticker} PO={po_val:.2f}%，{above_str}，{pos_str}（得分 {score:.0f}）：价格振荡动能偏强，多头趋势持续。"
        ),
        "neutral": (
            f"{ticker} PO={po_val:.2f}%，{above_str}，{pos_str}（得分 {score:.0f}）：均线振荡中性，趋势不明。"
        ),
        "bear": (
            f"{ticker} PO={po_val:.2f}%，{above_str}，{pos_str}（得分 {score:.0f}）：价格振荡动能偏弱，空头趋势占优。"
        ),
        "strong_bear": (
            f"{ticker} PO={po_val:.2f}%，{above_str}，{pos_str}（得分 {score:.0f}）：价格振荡动能极弱，短均线大幅跌破长均线。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算价格振荡器。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_po(ticker: str) -> POData:
    """Compute Price Oscillator for *ticker*.

    Never raises. Returns POData with data_available=False on failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return POData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    if hist.empty or "Close" not in hist.columns:
        return POData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 PO。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()

    if len(close) < _MIN_BARS:
        return POData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 PO。",
            as_of_date=as_of,
        )

    po_s, sig_s = _compute_po_series(close)

    po_val  = float(po_s.iloc[-1])
    sig_val = float(sig_s.iloc[-1])

    score  = _compute_po_score(po_val, sig_val, po_s)
    signal = _classify_signal(score)
    interp = _build_interpretation(
        ticker, signal, po_val, po_val > sig_val, po_val > 0, score
    )

    return POData(
        ticker=ticker,
        po_value=round(po_val, 4),
        signal_value=round(sig_val, 4),
        po_above_signal=po_val > sig_val,
        po_positive=po_val > 0,
        po_score=score,
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
