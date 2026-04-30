"""Hull Moving Average (HMA) engine — Phase F.69.

HMA Formula:
  WMA(n) = Weighted Moving Average over period n
  Raw     = 2 × WMA(n/2, close) − WMA(n, close)
  HMA     = WMA(sqrt(n), Raw)

  Default period: n=20

Score (0–100):
  40 pts  close > HMA  (price above hull)
  30 pts  HMA slope > 0  (hull rising in last 3 bars)
  30 pts  percentile rank of (close − HMA) / HMA in 252-bar window × 30

Never raises; degrades gracefully.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

HMASignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_PERIOD    = 20
_MIN_BARS  = _PERIOD * 3 + 5


@dataclass
class HMAData:
    ticker: str
    hma_value: float | None = None
    close_value: float | None = None
    price_above_hma: bool | None = None
    hma_rising: bool | None = None
    hma_score: float = 50.0
    signal: HMASignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wma(series: pd.Series, period: int) -> pd.Series:
    """Weighted moving average: linearly increasing weights."""
    weights = list(range(1, period + 1))
    wsum    = sum(weights)
    return series.rolling(period).apply(
        lambda x: sum(w * v for w, v in zip(weights, x)) / wsum,
        raw=True,
    )


def _compute_hma_series(
    close: pd.Series,
    period: int = _PERIOD,
) -> pd.Series:
    """Return HMA series of the same length as *close*."""
    half   = max(2, period // 2)
    sqrtn  = max(2, round(math.sqrt(period)))
    raw    = 2.0 * _wma(close, half) - _wma(close, period)
    hma    = _wma(raw, sqrtn).ffill().fillna(close)
    return hma


def _compute_hma_score(
    close_val: float,
    hma_val: float,
    hma_series: pd.Series,
    close_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Composite score 0–100."""
    above_pts = 40.0 if close_val > hma_val else 0.0

    # Slope: compare last HMA value to 3 bars ago
    recent = hma_series.dropna()
    if len(recent) >= 4:
        slope_pts = 30.0 if float(recent.iloc[-1]) > float(recent.iloc[-4]) else 0.0
    else:
        slope_pts = 15.0

    # Percentile rank of (close - HMA) / HMA
    ratio_series = ((close_series - hma_series) / hma_series.replace(0, float("nan"))).dropna()
    window       = ratio_series.iloc[-lookback:]
    current_ratio = (close_val - hma_val) / hma_val if hma_val != 0 else 0.0
    if len(window) < 10:
        pct_pts = 15.0
    else:
        pct_pts = float((window < current_ratio).mean()) * 30.0

    return round(above_pts + slope_pts + pct_pts, 1)


def _classify_signal(score: float | None) -> HMASignal:
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
    signal: HMASignal,
    close_val: float,
    hma_val: float,
    above: bool,
    rising: bool,
    score: float,
) -> str:
    above_str = "高于" if above else "低于"
    trend_str = "上升趋势" if rising else "下降趋势"
    labels: dict[HMASignal, str] = {
        "strong_bull": (
            f"{ticker} 收盘价={close_val:.2f}，{above_str} HMA({_PERIOD})={hma_val:.2f}，"
            f"HMA 呈{trend_str}（得分 {score:.0f}）：价格动能极强，趋势显著上行。"
        ),
        "bull": (
            f"{ticker} 收盘价={close_val:.2f}，{above_str} HMA({_PERIOD})={hma_val:.2f}，"
            f"HMA 呈{trend_str}（得分 {score:.0f}）：价格偏强，短期趋势向好。"
        ),
        "neutral": (
            f"{ticker} 收盘价={close_val:.2f}，{above_str} HMA({_PERIOD})={hma_val:.2f}，"
            f"HMA 呈{trend_str}（得分 {score:.0f}）：价格与均线接近，趋势中性。"
        ),
        "bear": (
            f"{ticker} 收盘价={close_val:.2f}，{above_str} HMA({_PERIOD})={hma_val:.2f}，"
            f"HMA 呈{trend_str}（得分 {score:.0f}）：价格偏弱，短期趋势走弱。"
        ),
        "strong_bear": (
            f"{ticker} 收盘价={close_val:.2f}，{above_str} HMA({_PERIOD})={hma_val:.2f}，"
            f"HMA 呈{trend_str}（得分 {score:.0f}）：价格动能极弱，趋势显著下行。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 HMA({_PERIOD})。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_hma(ticker: str, period: int = _PERIOD) -> HMAData:
    """Compute Hull Moving Average for *ticker*.

    Never raises. Returns HMAData with data_available=False on failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return HMAData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    if hist.empty or "Close" not in hist.columns:
        return HMAData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 HMA。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()

    if len(close) < _MIN_BARS:
        return HMAData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 HMA。",
            as_of_date=as_of,
        )

    hma_s = _compute_hma_series(close, period)

    close_val = float(close.iloc[-1])
    hma_val   = float(hma_s.iloc[-1])

    # Slope
    recent = hma_s.dropna()
    hma_rising = bool(len(recent) >= 4 and float(recent.iloc[-1]) > float(recent.iloc[-4]))

    score  = _compute_hma_score(close_val, hma_val, hma_s, close)
    signal = _classify_signal(score)
    interp = _build_interpretation(
        ticker, signal, close_val, hma_val,
        close_val > hma_val, hma_rising, score,
    )

    return HMAData(
        ticker=ticker,
        hma_value=round(hma_val, 4),
        close_value=round(close_val, 4),
        price_above_hma=close_val > hma_val,
        hma_rising=hma_rising,
        hma_score=score,
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
