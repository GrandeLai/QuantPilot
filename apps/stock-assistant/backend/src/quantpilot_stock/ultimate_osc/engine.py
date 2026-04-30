"""Ultimate Oscillator engine — Phase F.54.

BP  = Close − min(Low, PrevClose)
TR  = max(High, PrevClose) − min(Low, PrevClose)
Avg(n) = RollingSum(BP, n) / RollingSum(TR, n)
UO  = 100 × (4×Avg(7) + 2×Avg(14) + Avg(28)) / 7

Score = percentile rank of UO in last 252 bars × 100.

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

UltimateOscSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_FAST_PERIOD   = 7
_MID_PERIOD    = 14
_SLOW_PERIOD   = 28
_OVERBOUGHT    = 70.0
_OVERSOLD      = 30.0
_MIN_BARS      = _SLOW_PERIOD + 10


@dataclass
class UltimateOscData:
    ticker: str
    uo_value: float | None = None          # 0–100
    uo_overbought: bool = False            # UO > 70
    uo_oversold: bool = False              # UO < 30
    uo_score: float = 50.0               # 0–100 percentile
    signal: UltimateOscSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_uo_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    fast: int = _FAST_PERIOD,
    mid: int = _MID_PERIOD,
    slow: int = _SLOW_PERIOD,
) -> pd.Series:
    """Return Ultimate Oscillator series (0–100)."""
    prev_close = close.shift(1)

    true_low  = pd.concat([low, prev_close], axis=1).min(axis=1)
    true_high = pd.concat([high, prev_close], axis=1).max(axis=1)

    bp = close - true_low                  # Buying Pressure
    tr = true_high - true_low              # True Range (avoid div-by-zero)
    tr = tr.replace(0.0, float("nan"))

    def avg(n: int) -> pd.Series:
        return bp.rolling(n).sum() / tr.rolling(n).sum()

    uo = 100.0 * (4.0 * avg(fast) + 2.0 * avg(mid) + avg(slow)) / 7.0
    return uo.fillna(50.0)   # neutral fallback for NaN


def _compute_uo_score(
    uo_val: float,
    uo_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Percentile rank of uo_val within last *lookback* bars × 100."""
    window = uo_series.iloc[-lookback:].dropna()
    if len(window) < 10:
        # fallback: UO already 0-100, map directly
        return float(max(0.0, min(100.0, uo_val)))
    rank = float((window < uo_val).mean())
    return round(rank * 100.0, 1)


def _classify_signal(score: float | None) -> UltimateOscSignal:
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
    signal: UltimateOscSignal,
    uo: float,
    score: float,
    overbought: bool,
    oversold: bool,
) -> str:
    extreme = ""
    if overbought:
        extreme = "（超买区间，注意回调风险）"
    elif oversold:
        extreme = "（超卖区间，关注反弹机会）"

    labels: dict[UltimateOscSignal, str] = {
        "strong_bull": (
            f"{ticker} 终极振荡器 {uo:.1f}{extreme}（百分位 {score:.0f}）："
            f"多周期动量极强，趋势向上。"
        ),
        "bull": (
            f"{ticker} 终极振荡器 {uo:.1f}{extreme}（百分位 {score:.0f}）："
            f"多周期动量偏强，看涨信号。"
        ),
        "neutral": (
            f"{ticker} 终极振荡器 {uo:.1f}{extreme}（百分位 {score:.0f}）："
            f"多周期动量中性，无明显趋势。"
        ),
        "bear": (
            f"{ticker} 终极振荡器 {uo:.1f}{extreme}（百分位 {score:.0f}）："
            f"多周期动量偏弱，看跌信号。"
        ),
        "strong_bear": (
            f"{ticker} 终极振荡器 {uo:.1f}{extreme}（百分位 {score:.0f}）："
            f"多周期动量极弱，趋势向下。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算终极振荡器。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_ultimate_osc(ticker: str) -> UltimateOscData:
    """Compute Ultimate Oscillator for *ticker*.

    Never raises. Returns UltimateOscData with data_available=False on failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return UltimateOscData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    required = {"High", "Low", "Close"}
    if hist.empty or not required.issubset(hist.columns):
        return UltimateOscData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算终极振荡器。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()
    high  = hist["High"].loc[close.index].dropna()
    low   = hist["Low"].loc[close.index].dropna()

    common = close.index.intersection(high.index).intersection(low.index)
    close, high, low = close.loc[common], high.loc[common], low.loc[common]

    if len(close) < _MIN_BARS:
        return UltimateOscData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算终极振荡器。",
            as_of_date=as_of,
        )

    uo_series = _compute_uo_series(high, low, close)

    uo_val     = float(uo_series.iloc[-1])
    overbought = uo_val > _OVERBOUGHT
    oversold   = uo_val < _OVERSOLD

    score  = _compute_uo_score(uo_val, uo_series)
    signal = _classify_signal(score)
    interp = _build_interpretation(ticker, signal, uo_val, score, overbought, oversold)

    return UltimateOscData(
        ticker=ticker,
        uo_value=round(uo_val, 2),
        uo_overbought=overbought,
        uo_oversold=oversold,
        uo_score=round(score, 1),
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
