"""Mass Index engine — Phase F.67.

  EMA1 = EMA(9, High − Low)
  EMA2 = EMA(9, EMA1)
  MI   = Σ(EMA1 / EMA2)  over 25 bars

Reversal bulge: MI crosses above 27 then drops below 26.5.

Score (0–100):
  40 pts  MI < 26.5 (not in elevated-volatility zone)
  30 pts  MI trending down (5-bar delta < 0)
  30 pts  inverse percentile rank in 252-bar window × 30

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

MassIndexSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_EMA_PERIOD  = 9
_SUM_PERIOD  = 25
_BULGE_HIGH  = 27.0
_BULGE_LOW   = 26.5
_MIN_BARS    = _EMA_PERIOD * 2 + _SUM_PERIOD + 5


@dataclass
class MassIndexData:
    ticker: str
    mass_index: float | None = None         # current MI value
    in_bulge: bool | None = None            # MI > 27 (elevated volatility)
    trending_down: bool | None = None       # MI falling (5-bar delta < 0)
    reversal_signal: bool | None = None     # bulge completed (crossed ↑27 then ↓26.5)
    mi_score: float = 50.0                  # 0–100 composite
    signal: MassIndexSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_mi_series(
    high: pd.Series,
    low: pd.Series,
    ema_period: int = _EMA_PERIOD,
    sum_period: int = _SUM_PERIOD,
) -> pd.Series:
    """Return Mass Index series."""
    hl_range = (high - low).clip(lower=0.0)
    ema1 = hl_range.ewm(span=ema_period, adjust=False).mean()
    ema2 = ema1.ewm(span=ema_period, adjust=False).mean()

    ratio = (ema1 / ema2.replace(0.0, float("nan"))).fillna(1.0)
    mi    = ratio.rolling(sum_period).sum().ffill().fillna(sum_period)
    return mi


def _compute_mi_score(
    mi_val: float,
    mi_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Composite score 0–100 (lower MI = calmer market = higher score)."""
    calm_pts  = 40.0 if mi_val < _BULGE_LOW else 0.0

    window = mi_series.iloc[-lookback:].dropna()
    if len(window) < 10:
        trend_pts = 15.0
        pct_pts   = 15.0
    else:
        last5 = mi_series.iloc[-6:-1]
        trend_pts = 30.0 if (len(last5) > 0 and float(last5.iloc[-1]) > mi_val) else 0.0
        # inverse percentile: lower MI → higher score
        pct_pts = float((window > mi_val).mean()) * 30.0

    return round(calm_pts + trend_pts + pct_pts, 1)


def _detect_reversal(mi_series: pd.Series, window: int = 10) -> bool:
    """True if a reversal bulge completed: MI went above 27 then below 26.5."""
    recent = mi_series.iloc[-window:]
    if len(recent) < 3:
        return False
    went_above = bool((recent > _BULGE_HIGH).any())
    last_val   = float(recent.iloc[-1])
    return went_above and last_val < _BULGE_LOW


def _classify_signal(score: float | None) -> MassIndexSignal:
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
    signal: MassIndexSignal,
    mi_val: float,
    in_bulge: bool,
    trending_down: bool,
    reversal: bool,
    score: float,
) -> str:
    bulge_str   = "处于波动高峰区（>27）" if in_bulge else "波动平静（<26.5）"
    trend_str   = "向下（波动收敛）" if trending_down else "向上（波动扩张）"
    reversal_st = "⚠ 反转信号触发！" if reversal else ""
    labels: dict[MassIndexSignal, str] = {
        "strong_bull": (
            f"{ticker} MI={mi_val:.2f}，{bulge_str}，MI趋势{trend_str}（得分 {score:.0f}）{reversal_st}：市场极度平静，趋势延续概率高。"
        ),
        "bull": (
            f"{ticker} MI={mi_val:.2f}，{bulge_str}，MI趋势{trend_str}（得分 {score:.0f}）{reversal_st}：波动相对平稳，多头环境。"
        ),
        "neutral": (
            f"{ticker} MI={mi_val:.2f}，{bulge_str}，MI趋势{trend_str}（得分 {score:.0f}）{reversal_st}：波动中性，趋势不明。"
        ),
        "bear": (
            f"{ticker} MI={mi_val:.2f}，{bulge_str}，MI趋势{trend_str}（得分 {score:.0f}）{reversal_st}：波动偏大，需警惕反转风险。"
        ),
        "strong_bear": (
            f"{ticker} MI={mi_val:.2f}，{bulge_str}，MI趋势{trend_str}（得分 {score:.0f}）{reversal_st}：波动极大，反转风险极高。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 Mass Index。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_mass_index(ticker: str) -> MassIndexData:
    """Compute Mass Index for *ticker*.

    Never raises. Returns MassIndexData with data_available=False on failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return MassIndexData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    required = {"High", "Low", "Close"}
    if hist.empty or not required.issubset(hist.columns):
        return MassIndexData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 Mass Index。",
            as_of_date=as_of,
        )

    high  = hist["High"].dropna()
    low   = hist["Low"].loc[high.index].fillna(high)
    close = hist["Close"].dropna()
    common = high.index.intersection(low.index).intersection(close.index)
    high, low = high.loc[common], low.loc[common]

    if len(high) < _MIN_BARS:
        return MassIndexData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 Mass Index。",
            as_of_date=as_of,
        )

    mi_s     = _compute_mi_series(high, low)
    mi_val   = float(mi_s.iloc[-1])
    in_bulge = mi_val > _BULGE_HIGH

    # 5-bar trend
    if len(mi_s) >= 6:
        trending_down = float(mi_s.iloc[-6]) > mi_val
    else:
        trending_down = False

    reversal = _detect_reversal(mi_s)
    score    = _compute_mi_score(mi_val, mi_s)
    signal   = _classify_signal(score)
    interp   = _build_interpretation(
        ticker, signal, mi_val, in_bulge, trending_down, reversal, score
    )

    return MassIndexData(
        ticker=ticker,
        mass_index=round(mi_val, 3),
        in_bulge=in_bulge,
        trending_down=trending_down,
        reversal_signal=reversal,
        mi_score=score,
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
