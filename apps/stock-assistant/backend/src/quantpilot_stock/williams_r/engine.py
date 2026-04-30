"""Williams %R engine — Phase F.44.

Williams %R = (Highest_High_n - Close) / (Highest_High_n - Lowest_Low_n) × -100

  %R ∈ [-100, 0]
  %R > -20  → overbought (price near high of range)
  %R < -80  → oversold  (price near low of range)

Score = (100 + %R) / 100 × 100 → [0, 100].
  %R=0   (at high, bullish) → score=100
  %R=-50 (mid-range)        → score=50
  %R=-100 (at low, bearish) → score=0

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

WilliamsRSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]


@dataclass
class WilliamsRData:
    ticker: str
    williams_r: float | None = None      # Latest %R value [-100, 0]
    prev_williams_r: float | None = None # Previous bar %R
    wr_direction: str = ""               # "rising" | "falling" | "flat"
    overbought: bool = False             # %R > -20
    oversold: bool = False               # %R < -80
    wr_score: float = 50.0              # 0-100 composite score
    signal: WilliamsRSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_MIN_BARS = 20   # 14 (WR period) + 6 guard


def _compute_williams_r_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Return Williams %R series in [-100, 0]."""
    highest_high = high.rolling(period).max()
    lowest_low = low.rolling(period).min()

    hl_range = highest_high - lowest_low
    # Avoid division by zero (when all prices identical)
    wr = ((highest_high - close) / hl_range.replace(0.0, float("nan"))) * -100.0
    return wr.fillna(-50.0)  # neutral fallback


def _compute_wr_score(williams_r: float) -> float:
    """Map %R [-100, 0] to score [0, 100].

    score = (100 + %R) / 100 * 100
    """
    return float(max(0.0, min(100.0, (100.0 + williams_r) / 100.0 * 100.0)))


def _classify_signal(wr_score: float | None) -> WilliamsRSignal:
    if wr_score is None:
        return "no_data"
    if wr_score >= 80:
        return "strong_bull"
    if wr_score >= 60:
        return "bull"
    if wr_score >= 40:
        return "neutral"
    if wr_score >= 20:
        return "bear"
    return "strong_bear"


def _build_interpretation(
    ticker: str,
    signal: WilliamsRSignal,
    williams_r: float,
    overbought: bool,
    oversold: bool,
) -> str:
    labels: dict[WilliamsRSignal, str] = {
        "strong_bull": f"{ticker} Williams %R {williams_r:.1f}：价格接近 14 日最高点，多头动能强。",
        "bull": f"{ticker} Williams %R {williams_r:.1f}：价格偏高位运行，买盘占优。",
        "neutral": f"{ticker} Williams %R {williams_r:.1f}：价格处于波动区间中段，方向待定。",
        "bear": f"{ticker} Williams %R {williams_r:.1f}：价格偏低位运行，卖盘占优。",
        "strong_bear": f"{ticker} Williams %R {williams_r:.1f}：价格接近 14 日最低点，空头动能强。",
        "no_data": f"{ticker} 数据不足，无法计算 Williams %R。",
    }
    parts = [labels.get(signal, "")]
    if overbought:
        parts.append("（%R > -20，超买区，注意回调风险）")
    elif oversold:
        parts.append("（%R < -80，超卖区，关注反弹机会）")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_williams_r(ticker: str) -> WilliamsRData:
    """Compute Williams %R data for *ticker*.

    Never raises. Returns WilliamsRData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1y", interval="1d")
    except Exception:
        return WilliamsRData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    required = {"High", "Low", "Close"}
    if hist.empty or not required.issubset(hist.columns):
        return WilliamsRData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 Williams %R。",
            as_of_date=as_of,
        )

    high = hist["High"].dropna()
    low = hist["Low"].dropna()
    close = hist["Close"].dropna()

    common_idx = high.index.intersection(low.index).intersection(close.index)
    high = high.loc[common_idx]
    low = low.loc[common_idx]
    close = close.loc[common_idx]

    if len(close) < _MIN_BARS:
        return WilliamsRData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 Williams %R。",
            as_of_date=as_of,
        )

    wr_series = _compute_williams_r_series(high, low, close)

    wr_val = float(wr_series.iloc[-1])
    prev_wr = float(wr_series.iloc[-2]) if len(wr_series) >= 2 else None

    if prev_wr is not None:
        diff = wr_val - prev_wr
        if diff > 1.0:
            direction = "rising"   # %R increasing → moving toward 0 = bullish
        elif diff < -1.0:
            direction = "falling"
        else:
            direction = "flat"
    else:
        direction = "flat"

    overbought = wr_val > -20.0
    oversold = wr_val < -80.0

    wr_score = _compute_wr_score(wr_val)
    signal = _classify_signal(wr_score)
    interpretation = _build_interpretation(ticker, signal, wr_val, overbought, oversold)

    return WilliamsRData(
        ticker=ticker,
        williams_r=round(wr_val, 2),
        prev_williams_r=round(prev_wr, 2) if prev_wr is not None else None,
        wr_direction=direction,
        overbought=overbought,
        oversold=oversold,
        wr_score=round(wr_score, 1),
        signal=signal,
        interpretation=interpretation,
        as_of_date=as_of,
        data_available=True,
    )
