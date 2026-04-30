"""Schaff Trend Cycle (STC) engine — Phase F.71.

STC applies a double-smoothed Stochastic oscillator to a MACD line:

  MACD    = EMA(fast, close) − EMA(slow, close)
  K1      = Stochastic(MACD, cycle_period)  — 0..100
  D1      = EMA(smooth, K1)
  K2      = Stochastic(D1, cycle_period)
  STC     = EMA(smooth, K2)               — 0..100

  Defaults: fast=23, slow=50, cycle=10, smooth=3

Score (0–100):
  40 pts  STC > 25  (above buy threshold)
  30 pts  STC rising  (STC[n] > STC[n−3])
  30 pts  percentile rank of STC in 252-bar window × 30

Signal thresholds based on score (not STC value directly).

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

STCSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_FAST_PERIOD  = 23
_SLOW_PERIOD  = 50
_CYCLE_PERIOD = 10
_SMOOTH       = 3
_MIN_BARS     = _SLOW_PERIOD + _CYCLE_PERIOD + _SMOOTH * 2 + 10


@dataclass
class STCData:
    ticker: str
    stc_value: float | None = None
    stc_above_buy: bool | None = None    # STC > 25
    stc_rising: bool | None = None
    stc_score: float = 50.0
    signal: STCSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _stoch(series: pd.Series, period: int) -> pd.Series:
    """Raw Stochastic of a series: (val − low_n) / (high_n − low_n) × 100."""
    lo = series.rolling(period).min()
    hi = series.rolling(period).max()
    rng = (hi - lo).replace(0.0, float("nan"))
    return ((series - lo) / rng * 100.0).fillna(50.0).clip(0.0, 100.0)


def _compute_stc_series(
    close: pd.Series,
    fast: int = _FAST_PERIOD,
    slow: int = _SLOW_PERIOD,
    cycle: int = _CYCLE_PERIOD,
    smooth: int = _SMOOTH,
) -> pd.Series:
    """Return STC series (0–100) of the same length as *close*."""
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd     = ema_fast - ema_slow

    k1  = _stoch(macd, cycle)
    d1  = k1.ewm(span=smooth, adjust=False).mean()
    k2  = _stoch(d1, cycle)
    stc = k2.ewm(span=smooth, adjust=False).mean().clip(0.0, 100.0).fillna(50.0)

    return stc


def _compute_stc_score(
    stc_val: float,
    stc_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Composite score 0–100."""
    above_pts = 40.0 if stc_val > 25.0 else 0.0

    recent = stc_series.dropna()
    if len(recent) >= 4:
        slope_pts = 30.0 if float(recent.iloc[-1]) > float(recent.iloc[-4]) else 0.0
    else:
        slope_pts = 15.0

    window = stc_series.dropna().iloc[-lookback:]
    if len(window) < 10:
        pct_pts = 15.0
    else:
        pct_pts = float((window < stc_val).mean()) * 30.0

    return round(above_pts + slope_pts + pct_pts, 1)


def _classify_signal(score: float | None) -> STCSignal:
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
    signal: STCSignal,
    stc_val: float,
    above_buy: bool,
    rising: bool,
    score: float,
) -> str:
    buy_str   = "高于买入阈值(25)" if above_buy else "低于买入阈值(25)"
    trend_str = "上升" if rising else "下降"
    labels: dict[STCSignal, str] = {
        "strong_bull": (
            f"{ticker} STC={stc_val:.1f}，{buy_str}，趋势周期{trend_str}（得分 {score:.0f}）：趋势周期极强，买入信号明显。"
        ),
        "bull": (
            f"{ticker} STC={stc_val:.1f}，{buy_str}，趋势周期{trend_str}（得分 {score:.0f}）：趋势周期偏强，趋势向上。"
        ),
        "neutral": (
            f"{ticker} STC={stc_val:.1f}，{buy_str}，趋势周期{trend_str}（得分 {score:.0f}）：趋势周期中性，观望为主。"
        ),
        "bear": (
            f"{ticker} STC={stc_val:.1f}，{buy_str}，趋势周期{trend_str}（得分 {score:.0f}）：趋势周期偏弱，注意卖出信号。"
        ),
        "strong_bear": (
            f"{ticker} STC={stc_val:.1f}，{buy_str}，趋势周期{trend_str}（得分 {score:.0f}）：趋势周期极弱，卖出信号明显。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 STC 指标。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_stc(ticker: str) -> STCData:
    """Compute Schaff Trend Cycle for *ticker*.

    Never raises. Returns STCData with data_available=False on failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return STCData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    if hist.empty or "Close" not in hist.columns:
        return STCData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 STC。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()

    if len(close) < _MIN_BARS:
        return STCData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 STC。",
            as_of_date=as_of,
        )

    stc_s  = _compute_stc_series(close)
    stc_val = float(stc_s.iloc[-1])

    recent   = stc_s.dropna()
    stc_rising = bool(len(recent) >= 4 and float(recent.iloc[-1]) > float(recent.iloc[-4]))

    score  = _compute_stc_score(stc_val, stc_s)
    signal = _classify_signal(score)
    interp = _build_interpretation(
        ticker, signal, stc_val, stc_val > 25.0, stc_rising, score
    )

    return STCData(
        ticker=ticker,
        stc_value=round(stc_val, 2),
        stc_above_buy=stc_val > 25.0,
        stc_rising=stc_rising,
        stc_score=score,
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
