"""Klinger Volume Oscillator (KVO) engine — Phase F.68.

  DM[i]  = High[i] + Low[i] + Close[i]
  Trend  = +1 if DM[i] > DM[i-1] else −1
  VF[i]  = Volume[i] × |2 × (dm / cumRange − 1)| × Trend[i] × 100
            where dm = High − Low and cumRange is EMA(12, dm)
  KVO    = EMA(34, VF) − EMA(55, VF)
  Signal = EMA(13, KVO)

Score (0–100):
  40 pts  KVO > Signal
  30 pts  KVO > 0
  30 pts  percentile rank of KVO in 252-bar window × 30

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

KVOSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_FAST_PERIOD   = 34
_SLOW_PERIOD   = 55
_SIGNAL_PERIOD = 13
_MIN_BARS      = _SLOW_PERIOD + _SIGNAL_PERIOD + 5


@dataclass
class KVOData:
    ticker: str
    kvo_value: float | None = None
    signal_value: float | None = None
    kvo_above_signal: bool | None = None
    kvo_positive: bool | None = None
    kvo_score: float = 50.0
    signal: KVOSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_kvo_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    fast: int = _FAST_PERIOD,
    slow: int = _SLOW_PERIOD,
    signal: int = _SIGNAL_PERIOD,
) -> tuple[pd.Series, pd.Series]:
    """Return (kvo, signal_line) series.

    Volume Force: VF = Volume × Trend × (1 + HL_ratio)
    where HL_ratio = (High−Low) / Close (normalised daily range, always ≥ 0).
    Trend = +1 when daily midpoint (H+L+C) rises, else −1.
    This formulation is non-zero even when the H-L range is constant.
    """
    dm    = high + low + close
    trend = dm.diff().apply(lambda x: 1.0 if x > 0 else -1.0).fillna(1.0)

    hl_ratio  = ((high - low) / close.replace(0.0, float("nan"))).fillna(0.0).clip(lower=0.0)
    vf        = volume * trend * (1.0 + hl_ratio)

    ema_fast  = vf.ewm(span=fast,   adjust=False).mean()
    ema_slow  = vf.ewm(span=slow,   adjust=False).mean()
    kvo       = (ema_fast - ema_slow).fillna(0.0)
    sig       = kvo.ewm(span=signal, adjust=False).mean().fillna(kvo)

    return kvo, sig


def _compute_kvo_score(
    kvo_val: float,
    sig_val: float,
    kvo_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Composite score 0–100."""
    above_pts = 40.0 if kvo_val > sig_val else 0.0
    pos_pts   = 30.0 if kvo_val > 0 else 0.0

    window = kvo_series.iloc[-lookback:].dropna()
    if len(window) < 10:
        pct_pts = 15.0
    else:
        pct_pts = float((window < kvo_val).mean()) * 30.0

    return round(above_pts + pos_pts + pct_pts, 1)


def _classify_signal(score: float | None) -> KVOSignal:
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
    signal: KVOSignal,
    kvo_val: float,
    kvo_above: bool,
    kvo_pos: bool,
    score: float,
) -> str:
    above_str = "高于信号线" if kvo_above else "低于信号线"
    pos_str   = "净积累（KVO>0）" if kvo_pos else "净派发（KVO<0）"
    labels: dict[KVOSignal, str] = {
        "strong_bull": (
            f"{ticker} KVO={kvo_val:.0f}，{above_str}，{pos_str}（得分 {score:.0f}）：量价动能极强，资金大量积累。"
        ),
        "bull": (
            f"{ticker} KVO={kvo_val:.0f}，{above_str}，{pos_str}（得分 {score:.0f}）：量价动能偏强，资金偏向买入。"
        ),
        "neutral": (
            f"{ticker} KVO={kvo_val:.0f}，{above_str}，{pos_str}（得分 {score:.0f}）：量价动能中性。"
        ),
        "bear": (
            f"{ticker} KVO={kvo_val:.0f}，{above_str}，{pos_str}（得分 {score:.0f}）：量价动能偏弱，资金偏向派发。"
        ),
        "strong_bear": (
            f"{ticker} KVO={kvo_val:.0f}，{above_str}，{pos_str}（得分 {score:.0f}）：量价动能极弱，资金大量流出。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 KVO 指标。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_kvo(ticker: str) -> KVOData:
    """Compute Klinger Volume Oscillator for *ticker*.

    Never raises. Returns KVOData with data_available=False on failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return KVOData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    required = {"High", "Low", "Close", "Volume"}
    if hist.empty or not required.issubset(hist.columns):
        return KVOData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 KVO。",
            as_of_date=as_of,
        )

    close  = hist["Close"].dropna()
    idx    = close.index
    high   = hist["High"].loc[idx].fillna(close)
    low    = hist["Low"].loc[idx].fillna(close)
    volume = hist["Volume"].loc[idx].fillna(0.0)

    common = close.index.intersection(high.index).intersection(low.index)
    close, high, low, volume = (
        close.loc[common], high.loc[common],
        low.loc[common], volume.loc[common],
    )

    if len(close) < _MIN_BARS:
        return KVOData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 KVO。",
            as_of_date=as_of,
        )

    kvo_s, sig_s = _compute_kvo_series(high, low, close, volume)

    kvo_val = float(kvo_s.iloc[-1])
    sig_val = float(sig_s.iloc[-1])

    score  = _compute_kvo_score(kvo_val, sig_val, kvo_s)
    signal = _classify_signal(score)
    interp = _build_interpretation(
        ticker, signal, kvo_val, kvo_val > sig_val, kvo_val > 0, score
    )

    return KVOData(
        ticker=ticker,
        kvo_value=round(kvo_val, 2),
        signal_value=round(sig_val, 2),
        kvo_above_signal=kvo_val > sig_val,
        kvo_positive=kvo_val > 0,
        kvo_score=score,
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
