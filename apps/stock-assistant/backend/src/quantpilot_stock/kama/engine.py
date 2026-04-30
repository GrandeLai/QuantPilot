"""Kaufman Adaptive Moving Average (KAMA) engine — Phase F.70.

KAMA Formula (Perry Kaufman, 1998):
  ER[n]   = |Close[n] − Close[n−period]| / Σ|Close[i] − Close[i−1]|  (efficiency ratio)
  fast_sc = 2 / (fast_period + 1)   # default fast_period = 2
  slow_sc = 2 / (slow_period + 1)   # default slow_period = 30
  SC[n]   = (ER[n] × (fast_sc − slow_sc) + slow_sc) ** 2
  KAMA[n] = KAMA[n−1] + SC[n] × (Close[n] − KAMA[n−1])

  Defaults: period=10, fast=2, slow=30

Score (0–100):
  40 pts  close > KAMA  (price above adaptive MA)
  30 pts  KAMA slope > 0  (KAMA rising, last 3 bars)
  30 pts  percentile rank of (close − KAMA) / KAMA in 252-bar window × 30

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import numpy as np
import pandas as pd
import yfinance as yf

KAMASignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_PERIOD      = 10
_FAST_PERIOD = 2
_SLOW_PERIOD = 30
_MIN_BARS    = _PERIOD + _SLOW_PERIOD + 10


@dataclass
class KAMAData:
    ticker: str
    kama_value: float | None = None
    close_value: float | None = None
    price_above_kama: bool | None = None
    kama_rising: bool | None = None
    kama_score: float = 50.0
    signal: KAMASignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_kama_series(
    close: pd.Series,
    period: int = _PERIOD,
    fast: int = _FAST_PERIOD,
    slow: int = _SLOW_PERIOD,
) -> pd.Series:
    """Return KAMA series of the same length as *close*."""
    fast_sc = 2.0 / (fast + 1)
    slow_sc = 2.0 / (slow + 1)

    prices = close.to_numpy(dtype=float)
    n      = len(prices)
    kama   = np.full(n, np.nan)

    # Initialise at first valid index
    kama[period - 1] = prices[period - 1]

    for i in range(period, n):
        direction = abs(prices[i] - prices[i - period])
        volatility = np.sum(np.abs(np.diff(prices[i - period: i + 1])))
        er  = direction / volatility if volatility > 0 else 0.0
        sc  = (er * (fast_sc - slow_sc) + slow_sc) ** 2
        kama[i] = kama[i - 1] + sc * (prices[i] - kama[i - 1])

    result = pd.Series(kama, index=close.index)
    return result.ffill().fillna(close)


def _compute_kama_score(
    close_val: float,
    kama_val: float,
    kama_series: pd.Series,
    close_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Composite score 0–100."""
    above_pts = 40.0 if close_val > kama_val else 0.0

    # Slope: last vs 3 bars ago
    recent = kama_series.dropna()
    if len(recent) >= 4:
        slope_pts = 30.0 if float(recent.iloc[-1]) > float(recent.iloc[-4]) else 0.0
    else:
        slope_pts = 15.0

    # Percentile rank
    ratio_series = ((close_series - kama_series) / kama_series.replace(0, float("nan"))).dropna()
    window       = ratio_series.iloc[-lookback:]
    current_r    = (close_val - kama_val) / kama_val if kama_val != 0 else 0.0
    if len(window) < 10:
        pct_pts = 15.0
    else:
        pct_pts = float((window < current_r).mean()) * 30.0

    return round(above_pts + slope_pts + pct_pts, 1)


def _classify_signal(score: float | None) -> KAMASignal:
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
    signal: KAMASignal,
    close_val: float,
    kama_val: float,
    above: bool,
    rising: bool,
    score: float,
) -> str:
    above_str = "高于" if above else "低于"
    trend_str = "上升" if rising else "下降"
    labels: dict[KAMASignal, str] = {
        "strong_bull": (
            f"{ticker} 收盘价={close_val:.2f}，{above_str} KAMA({_PERIOD})={kama_val:.2f}，"
            f"KAMA 趋势{trend_str}（得分 {score:.0f}）：自适应均线动能极强，趋势稳固上行。"
        ),
        "bull": (
            f"{ticker} 收盘价={close_val:.2f}，{above_str} KAMA({_PERIOD})={kama_val:.2f}，"
            f"KAMA 趋势{trend_str}（得分 {score:.0f}）：自适应均线偏强，短期趋势向好。"
        ),
        "neutral": (
            f"{ticker} 收盘价={close_val:.2f}，{above_str} KAMA({_PERIOD})={kama_val:.2f}，"
            f"KAMA 趋势{trend_str}（得分 {score:.0f}）：市场效率中性，自适应均线平稳。"
        ),
        "bear": (
            f"{ticker} 收盘价={close_val:.2f}，{above_str} KAMA({_PERIOD})={kama_val:.2f}，"
            f"KAMA 趋势{trend_str}（得分 {score:.0f}）：自适应均线偏弱，短期趋势走弱。"
        ),
        "strong_bear": (
            f"{ticker} 收盘价={close_val:.2f}，{above_str} KAMA({_PERIOD})={kama_val:.2f}，"
            f"KAMA 趋势{trend_str}（得分 {score:.0f}）：自适应均线极弱，趋势显著下行。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 KAMA({_PERIOD})。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_kama(ticker: str, period: int = _PERIOD) -> KAMAData:
    """Compute KAMA for *ticker*.

    Never raises. Returns KAMAData with data_available=False on failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return KAMAData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    if hist.empty or "Close" not in hist.columns:
        return KAMAData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 KAMA。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()

    if len(close) < _MIN_BARS:
        return KAMAData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 KAMA。",
            as_of_date=as_of,
        )

    kama_s = _compute_kama_series(close, period)

    close_val = float(close.iloc[-1])
    kama_val  = float(kama_s.iloc[-1])

    recent     = kama_s.dropna()
    kama_rising = bool(len(recent) >= 4 and float(recent.iloc[-1]) > float(recent.iloc[-4]))

    score  = _compute_kama_score(close_val, kama_val, kama_s, close)
    signal = _classify_signal(score)
    interp = _build_interpretation(
        ticker, signal, close_val, kama_val,
        close_val > kama_val, kama_rising, score,
    )

    return KAMAData(
        ticker=ticker,
        kama_value=round(kama_val, 4),
        close_value=round(close_val, 4),
        price_above_kama=close_val > kama_val,
        kama_rising=kama_rising,
        kama_score=score,
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
