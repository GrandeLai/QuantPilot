"""Price Volume Trend (PVT) engine — Phase F.64.

Cumulative volume-weighted price momentum:

  PVT     = Σ ((Close[i] − Close[i-1]) / Close[i-1]) × Volume[i]
  Signal  = SMA(21, PVT)
  Slope   = (PVT − PVT.shift(5)) / 5   (5-bar rate of change)

Score (0–100):
  40 pts  PVT > Signal (accumulation dominating)
  30 pts  Slope > 0 (PVT rising)
  30 pts  percentile rank of Slope in 252-bar window × 30

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

PVTSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_SIGNAL_PERIOD = 21
_SLOPE_PERIOD  = 5
_MIN_BARS      = _SIGNAL_PERIOD + _SLOPE_PERIOD + 5


@dataclass
class PVTData:
    ticker: str
    pvt_above_signal: bool | None = None   # PVT > Signal
    pvt_slope_positive: bool | None = None # Slope > 0
    pvt_score: float = 50.0               # 0–100 composite
    signal: PVTSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_pvt_series(
    close: pd.Series,
    volume: pd.Series,
    signal_period: int = _SIGNAL_PERIOD,
    slope_period: int = _SLOPE_PERIOD,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Return (pvt, signal, slope) series."""
    pct_change = close.pct_change().fillna(0.0)
    pvt        = (pct_change * volume).cumsum()
    signal     = pvt.rolling(signal_period).mean().ffill().fillna(pvt)
    slope      = (pvt - pvt.shift(slope_period)).ffill().fillna(0.0)
    return pvt, signal, slope


def _compute_pvt_score(
    pvt_val: float,
    sig_val: float,
    slope_val: float,
    slope_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Composite score 0–100."""
    above_pts = 40.0 if pvt_val > sig_val else 0.0
    slope_pts = 30.0 if slope_val > 0 else 0.0

    window = slope_series.iloc[-lookback:].dropna()
    if len(window) < 10:
        pct_pts = 15.0
    else:
        pct_pts = float((window < slope_val).mean()) * 30.0

    return round(above_pts + slope_pts + pct_pts, 1)


def _classify_signal(score: float | None) -> PVTSignal:
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
    signal: PVTSignal,
    pvt_above: bool,
    slope_pos: bool,
    score: float,
) -> str:
    pos_str   = "高于信号线（资金净流入）" if pvt_above else "低于信号线（资金净流出）"
    slope_str = "向上（动量增强）" if slope_pos else "向下（动量减弱）"
    labels: dict[PVTSignal, str] = {
        "strong_bull": (
            f"{ticker} PVT {pos_str}，斜率{slope_str}（得分 {score:.0f}）：量价趋势极强，资金积累显著。"
        ),
        "bull": (
            f"{ticker} PVT {pos_str}，斜率{slope_str}（得分 {score:.0f}）：量价趋势偏强，资金偏向买入。"
        ),
        "neutral": (
            f"{ticker} PVT {pos_str}，斜率{slope_str}（得分 {score:.0f}）：量价趋势中性。"
        ),
        "bear": (
            f"{ticker} PVT {pos_str}，斜率{slope_str}（得分 {score:.0f}）：量价趋势偏弱，资金开始流出。"
        ),
        "strong_bear": (
            f"{ticker} PVT {pos_str}，斜率{slope_str}（得分 {score:.0f}）：量价趋势极弱，资金持续流出。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 PVT 指标。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_pvt(ticker: str) -> PVTData:
    """Compute Price Volume Trend for *ticker*.

    Never raises. Returns PVTData with data_available=False on failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return PVTData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    required = {"Close", "Volume"}
    if hist.empty or not required.issubset(hist.columns):
        return PVTData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 PVT。",
            as_of_date=as_of,
        )

    close  = hist["Close"].dropna()
    volume = hist["Volume"].loc[close.index].fillna(0.0)

    common = close.index.intersection(volume.index)
    close, volume = close.loc[common], volume.loc[common]

    if len(close) < _MIN_BARS:
        return PVTData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 PVT。",
            as_of_date=as_of,
        )

    pvt_s, sig_s, slope_s = _compute_pvt_series(close, volume)

    pvt_val   = float(pvt_s.iloc[-1])
    sig_val   = float(sig_s.iloc[-1])
    slope_val = float(slope_s.iloc[-1])

    score   = _compute_pvt_score(pvt_val, sig_val, slope_val, slope_s)
    signal  = _classify_signal(score)
    interp  = _build_interpretation(ticker, signal, pvt_val > sig_val, slope_val > 0, score)

    return PVTData(
        ticker=ticker,
        pvt_above_signal=pvt_val > sig_val,
        pvt_slope_positive=slope_val > 0,
        pvt_score=score,
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
