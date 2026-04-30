"""Supertrend engine — Phase F.55.

ATR(n)    = Wilder EMA of True Range (n=10)
UpperBand = (H+L)/2 + Factor × ATR   (Factor=3.0)
LowerBand = (H+L)/2 − Factor × ATR
Supertrend = LowerBand when UP; UpperBand when DOWN.
Trend flips UP when Close > prev UpperBand.
Trend flips DOWN when Close < prev LowerBand.

Score = percentile rank of distance_pct = (Close - ST) / Close × 100
        in last 252 bars × 100.

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import numpy as np
import pandas as pd
import yfinance as yf

SupertrendSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_ATR_PERIOD  = 10
_FACTOR      = 3.0
_MIN_BARS    = _ATR_PERIOD * 3 + 5   # buffer for Wilder warm-up


@dataclass
class SupertrendData:
    ticker: str
    supertrend_value: float | None = None   # Supertrend line price
    distance_pct: float | None = None       # (Close - ST) / Close × 100
    supertrend_bullish: bool = False        # close > supertrend
    supertrend_score: float = 50.0         # 0–100 percentile
    signal: SupertrendSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    """Wilder EMA ATR."""
    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low,
         (high - prev_close).abs(),
         (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()


def _compute_supertrend_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = _ATR_PERIOD,
    factor: float = _FACTOR,
) -> tuple[pd.Series, pd.Series]:
    """Return (supertrend_series, distance_pct_series).

    supertrend_series: actual Supertrend line value.
    distance_pct_series: (Close - ST) / Close × 100.
    """
    atr = _compute_atr(high, low, close, period)
    hl2 = (high + low) / 2.0

    upper_basic = hl2 + factor * atr
    lower_basic = hl2 - factor * atr

    n = len(close)
    supertrend = np.full(n, float("nan"))
    upper      = upper_basic.values.copy()
    lower      = lower_basic.values.copy()
    trend      = np.ones(n, dtype=int)   # 1=up, -1=down

    for i in range(1, n):
        # Adjust bands
        if not np.isnan(upper[i - 1]):
            upper[i] = min(upper[i], upper[i - 1]) if close.iloc[i - 1] <= upper[i - 1] else upper[i]
        if not np.isnan(lower[i - 1]):
            lower[i] = max(lower[i], lower[i - 1]) if close.iloc[i - 1] >= lower[i - 1] else lower[i]

        # Determine trend
        if np.isnan(supertrend[i - 1]):
            trend[i] = 1
            supertrend[i] = lower[i]
        elif supertrend[i - 1] == upper[i - 1]:
            trend[i] = 1 if close.iloc[i] > upper[i] else -1
        else:
            trend[i] = -1 if close.iloc[i] < lower[i] else 1

        supertrend[i] = lower[i] if trend[i] == 1 else upper[i]

    st_series   = pd.Series(supertrend, index=close.index)
    close_arr   = close.values
    dist_pct    = np.where(
        close_arr != 0,
        (close_arr - supertrend) / close_arr * 100.0,
        0.0,
    )
    dist_series = pd.Series(dist_pct, index=close.index)
    dist_series = dist_series.fillna(0.0)
    return st_series, dist_series


def _compute_supertrend_score(
    dist_val: float,
    dist_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Percentile rank of dist_val in last *lookback* bars × 100."""
    window = dist_series.iloc[-lookback:].dropna()
    if len(window) < 10:
        return float(max(0.0, min(100.0, (dist_val + 5.0) / 10.0 * 100.0)))
    rank = float((window < dist_val).mean())
    return round(rank * 100.0, 1)


def _classify_signal(score: float | None) -> SupertrendSignal:
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
    signal: SupertrendSignal,
    st_val: float,
    dist_pct: float,
    score: float,
    bullish: bool,
) -> str:
    trend_label = "上升趋势" if bullish else "下降趋势"
    labels: dict[SupertrendSignal, str] = {
        "strong_bull": (
            f"{ticker} Supertrend {st_val:.2f}，距离 {dist_pct:+.2f}%（百分位 {score:.0f}）："
            f"{trend_label}极强，价格大幅高于 Supertrend。"
        ),
        "bull": (
            f"{ticker} Supertrend {st_val:.2f}，距离 {dist_pct:+.2f}%（百分位 {score:.0f}）："
            f"{trend_label}偏强，价格站稳 Supertrend 上方。"
        ),
        "neutral": (
            f"{ticker} Supertrend {st_val:.2f}，距离 {dist_pct:+.2f}%（百分位 {score:.0f}）："
            f"趋势中性，价格接近 Supertrend。"
        ),
        "bear": (
            f"{ticker} Supertrend {st_val:.2f}，距离 {dist_pct:+.2f}%（百分位 {score:.0f}）："
            f"{trend_label}偏弱，价格跌破 Supertrend。"
        ),
        "strong_bear": (
            f"{ticker} Supertrend {st_val:.2f}，距离 {dist_pct:+.2f}%（百分位 {score:.0f}）："
            f"{trend_label}极强，价格大幅低于 Supertrend。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 Supertrend。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_supertrend(ticker: str) -> SupertrendData:
    """Compute Supertrend for *ticker*.

    Never raises. Returns SupertrendData with data_available=False on failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return SupertrendData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    required = {"High", "Low", "Close"}
    if hist.empty or not required.issubset(hist.columns):
        return SupertrendData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 Supertrend。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()
    high  = hist["High"].loc[close.index].dropna()
    low   = hist["Low"].loc[close.index].dropna()

    common = close.index.intersection(high.index).intersection(low.index)
    close, high, low = close.loc[common], high.loc[common], low.loc[common]

    if len(close) < _MIN_BARS:
        return SupertrendData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 Supertrend。",
            as_of_date=as_of,
        )

    st_series, dist_series = _compute_supertrend_series(high, low, close)

    st_val   = float(st_series.iloc[-1])
    dist_val = float(dist_series.iloc[-1])
    bullish  = dist_val > 0.0

    score  = _compute_supertrend_score(dist_val, dist_series)
    signal = _classify_signal(score)
    interp = _build_interpretation(ticker, signal, st_val, dist_val, score, bullish)

    return SupertrendData(
        ticker=ticker,
        supertrend_value=round(st_val, 4),
        distance_pct=round(dist_val, 4),
        supertrend_bullish=bullish,
        supertrend_score=round(score, 1),
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
