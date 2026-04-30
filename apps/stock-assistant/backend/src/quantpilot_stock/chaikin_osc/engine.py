"""Chaikin Oscillator engine — Phase F.61.

Measures momentum of the Accumulation/Distribution Line:

  MFM (Money Flow Multiplier) = ((Close - Low) - (High - Close)) / (High - Low)
  MFV (Money Flow Volume)     = MFM * Volume
  AD  (Accumulation/Distribution) = cumulative MFV
  Chaikin Osc = EMA(3, AD) - EMA(10, AD)

Positive oscillator → money is flowing into the security (accumulation).
Negative oscillator → money is flowing out (distribution).

Score = percentile rank of Chaikin Osc in last 252 bars × 100.

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

ChaikinOscSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_FAST     = 3
_SLOW     = 10
_MIN_BARS = _SLOW + 5


@dataclass
class ChaikinOscData:
    ticker: str
    chaikin_osc: float | None = None        # Current oscillator value
    osc_positive: bool | None = None        # Oscillator > 0
    chaikin_score: float = 50.0            # 0–100 percentile
    signal: ChaikinOscSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_ad_line(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
) -> pd.Series:
    """Accumulation/Distribution Line."""
    hl_range = (high - low).replace(0.0, float("nan"))
    mfm = ((close - low) - (high - close)) / hl_range
    mfm = mfm.fillna(0.0)
    mfv = mfm * volume
    return mfv.cumsum()


def _compute_chaikin_osc_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
) -> pd.Series:
    """Return Chaikin Oscillator series."""
    ad  = _compute_ad_line(high, low, close, volume)
    ema3  = ad.ewm(span=_FAST,  adjust=False).mean()
    ema10 = ad.ewm(span=_SLOW, adjust=False).mean()
    return (ema3 - ema10).ffill().fillna(0.0)


def _compute_chaikin_score(
    osc_val: float,
    osc_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Percentile rank of osc_val in last *lookback* bars × 100."""
    window = osc_series.iloc[-lookback:].dropna()
    if len(window) < 10:
        return 50.0
    rank = float((window < osc_val).mean())
    return round(rank * 100.0, 1)


def _classify_signal(score: float | None) -> ChaikinOscSignal:
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
    signal: ChaikinOscSignal,
    osc_val: float,
    score: float,
) -> str:
    pos_str  = "正值（资金净流入）" if osc_val > 0 else "负值（资金净流出）"
    labels: dict[ChaikinOscSignal, str] = {
        "strong_bull": (
            f"{ticker} 钱龙震荡指标={osc_val:.2f}（{pos_str}，百分位 {score:.0f}）：资金积累极强，看涨信号明显。"
        ),
        "bull": (
            f"{ticker} 钱龙震荡指标={osc_val:.2f}（{pos_str}，百分位 {score:.0f}）：资金持续流入，偏多格局。"
        ),
        "neutral": (
            f"{ticker} 钱龙震荡指标={osc_val:.2f}（{pos_str}，百分位 {score:.0f}）：资金进出均衡，趋势中性。"
        ),
        "bear": (
            f"{ticker} 钱龙震荡指标={osc_val:.2f}（{pos_str}，百分位 {score:.0f}）：资金开始流出，偏空格局。"
        ),
        "strong_bear": (
            f"{ticker} 钱龙震荡指标={osc_val:.2f}（{pos_str}，百分位 {score:.0f}）：资金持续派发，看跌信号明显。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算钱龙震荡指标。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_chaikin_osc(ticker: str) -> ChaikinOscData:
    """Compute Chaikin Oscillator for *ticker*.

    Never raises. Returns ChaikinOscData with data_available=False on failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return ChaikinOscData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    required = {"High", "Low", "Close", "Volume"}
    if hist.empty or not required.issubset(hist.columns):
        return ChaikinOscData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算钱龙震荡指标。",
            as_of_date=as_of,
        )

    close  = hist["Close"].dropna()
    high   = hist["High"].loc[close.index].dropna()
    low    = hist["Low"].loc[close.index].dropna()
    volume = hist["Volume"].loc[close.index].fillna(0.0)

    common = close.index.intersection(high.index).intersection(low.index)
    close, high, low = close.loc[common], high.loc[common], low.loc[common]
    volume = volume.loc[common]

    if len(close) < _MIN_BARS:
        return ChaikinOscData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算钱龙震荡指标。",
            as_of_date=as_of,
        )

    osc_s   = _compute_chaikin_osc_series(high, low, close, volume)
    osc_val = float(osc_s.iloc[-1])
    score   = _compute_chaikin_score(osc_val, osc_s)
    signal  = _classify_signal(score)
    interp  = _build_interpretation(ticker, signal, osc_val, score)

    return ChaikinOscData(
        ticker=ticker,
        chaikin_osc=round(osc_val, 2),
        osc_positive=osc_val > 0,
        chaikin_score=score,
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
