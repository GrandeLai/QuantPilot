"""Elder Ray Index engine — Phase F.62.

Dr. Alexander Elder's indicator measuring buying/selling pressure vs trend:

  EMA(13, Close)  = base trend line (13-period exponential moving average)
  Bull Power      = High − EMA(13)   [positive → bulls above trend]
  Bear Power      = Low  − EMA(13)   [negative → bears below trend]

Score (0–100):
  40 pts  Bull Power > 0 (price high above EMA → bullish)
  30 pts  Bear Power rising (current > previous → bears weakening)
  30 pts  percentile rank of (Bull Power − Bear Power) in 252-bar window

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

ElderRaySignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_EMA_PERIOD = 13
_MIN_BARS   = _EMA_PERIOD + 5


@dataclass
class ElderRayData:
    ticker: str
    bull_power: float | None = None        # High - EMA(13)
    bear_power: float | None = None        # Low  - EMA(13)
    ema13: float | None = None             # Base EMA
    bull_positive: bool | None = None      # Bull Power > 0
    bear_rising: bool | None = None        # Bear Power rising (less negative)
    elder_ray_score: float = 50.0         # 0–100 composite
    signal: ElderRaySignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_elder_ray_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = _EMA_PERIOD,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Return (bull_power, bear_power, ema) series."""
    ema        = close.ewm(span=period, adjust=False).mean()
    bull_power = high - ema
    bear_power = low  - ema
    return bull_power, bear_power, ema


def _compute_elder_ray_score(
    bull_val: float,
    bear_val: float,
    bear_prev: float,
    combined_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Composite score 0–100."""
    bull_pts = 40.0 if bull_val > 0 else 0.0
    bear_pts = 30.0 if bear_val > bear_prev else 0.0

    window = combined_series.iloc[-lookback:].dropna()
    combined_val = bull_val - bear_val  # spread (higher = more bullish)
    if len(window) < 10:
        pct_pts = 15.0
    else:
        pct_pts = float((window < combined_val).mean()) * 30.0

    return round(bull_pts + bear_pts + pct_pts, 1)


def _classify_signal(score: float | None) -> ElderRaySignal:
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
    signal: ElderRaySignal,
    bull_val: float,
    bear_val: float,
    score: float,
) -> str:
    bull_str = f"多头力量={bull_val:+.2f}（{'高于' if bull_val > 0 else '低于'}EMA）"
    bear_str = f"空头力量={bear_val:+.2f}（{'向上' if bear_val > 0 else '向下'}偏离EMA）"
    labels: dict[ElderRaySignal, str] = {
        "strong_bull": (
            f"{ticker} {bull_str}，{bear_str}（得分 {score:.0f}）：多头极强，买盘压力明显。"
        ),
        "bull": (
            f"{ticker} {bull_str}，{bear_str}（得分 {score:.0f}）：多头力量偏强，趋势偏多。"
        ),
        "neutral": (
            f"{ticker} {bull_str}，{bear_str}（得分 {score:.0f}）：多空力量均衡，趋势中性。"
        ),
        "bear": (
            f"{ticker} {bull_str}，{bear_str}（得分 {score:.0f}）：空头力量偏强，趋势偏空。"
        ),
        "strong_bear": (
            f"{ticker} {bull_str}，{bear_str}（得分 {score:.0f}）：空头极强，卖压明显。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 Elder Ray 指标。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_elder_ray(ticker: str) -> ElderRayData:
    """Compute Elder Ray Index for *ticker*.

    Never raises. Returns ElderRayData with data_available=False on failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return ElderRayData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    required = {"High", "Low", "Close"}
    if hist.empty or not required.issubset(hist.columns):
        return ElderRayData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 Elder Ray 指标。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()
    high  = hist["High"].loc[close.index].dropna()
    low   = hist["Low"].loc[close.index].dropna()

    common = close.index.intersection(high.index).intersection(low.index)
    close, high, low = close.loc[common], high.loc[common], low.loc[common]

    if len(close) < _MIN_BARS:
        return ElderRayData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 Elder Ray 指标。",
            as_of_date=as_of,
        )

    bull_s, bear_s, ema_s = _compute_elder_ray_series(high, low, close)

    bull_val  = float(bull_s.iloc[-1])
    bear_val  = float(bear_s.iloc[-1])
    bear_prev = float(bear_s.iloc[-2]) if len(bear_s) >= 2 else bear_val
    ema_val   = float(ema_s.iloc[-1])

    # Combined spread series for percentile
    combined_s = bull_s - bear_s

    score  = _compute_elder_ray_score(bull_val, bear_val, bear_prev, combined_s)
    signal = _classify_signal(score)
    interp = _build_interpretation(ticker, signal, bull_val, bear_val, score)

    return ElderRayData(
        ticker=ticker,
        bull_power=round(bull_val, 4),
        bear_power=round(bear_val, 4),
        ema13=round(ema_val, 4),
        bull_positive=bull_val > 0,
        bear_rising=bear_val > bear_prev,
        elder_ray_score=score,
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
