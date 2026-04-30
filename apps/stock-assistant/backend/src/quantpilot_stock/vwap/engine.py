"""VWAP engine — Phase F.49.

Rolling 20-day VWAP (daily bars):
  TP   = (High + Low + Close) / 3
  VWAP = rolling_sum(TP × Volume, 20) / rolling_sum(Volume, 20)

Score = percentile rank of (Close/VWAP − 1) within last 252 bars × 100.
  Positive deviation (above VWAP) → higher rank.

Secondary:
  vwap_deviation_pct : (Close − VWAP) / VWAP × 100
  above_vwap         : Close > VWAP
  vwap_slope         : "rising" | "falling" | "flat"  (VWAP[−1] vs VWAP[−6])

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

VWAPSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_VWAP_PERIOD = 20
_SLOPE_LOOKBACK = 5   # bars back to compare for slope
_MIN_BARS = 30


@dataclass
class VWAPData:
    ticker: str
    vwap: float | None = None              # Latest rolling VWAP
    vwap_deviation_pct: float | None = None  # (Close − VWAP) / VWAP × 100
    above_vwap: bool = False               # Close > VWAP
    vwap_slope: str = ""                   # "rising" | "falling" | "flat"
    vwap_score: float = 50.0              # 0-100 percentile-based score
    signal: VWAPSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_vwap_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    period: int = _VWAP_PERIOD,
) -> pd.Series:
    """Return rolling VWAP series."""
    tp = (high + low + close) / 3.0
    tpv = tp * volume.astype(float)
    vol_f = volume.astype(float)
    tpv_sum = tpv.rolling(period).sum()
    vol_sum = vol_f.rolling(period).sum()
    vwap = tpv_sum / vol_sum.replace(0.0, float("nan"))
    return vwap.ffill().fillna(close)


def _compute_deviation_series(close: pd.Series, vwap: pd.Series) -> pd.Series:
    """(Close − VWAP) / VWAP × 100; 0 where VWAP is 0/NaN."""
    safe_vwap = vwap.replace(0.0, float("nan"))
    dev = (close - vwap) / safe_vwap * 100.0
    return dev.fillna(0.0)


def _compute_vwap_score(
    dev_val: float,
    dev_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Percentile rank of dev_val within last *lookback* bars × 100."""
    window = dev_series.iloc[-lookback:].dropna()
    if len(window) < 10:
        # Fallback: linear map ±10 % → 0-100
        return float(max(0.0, min(100.0, (dev_val + 10.0) / 20.0 * 100.0)))
    rank = float((window < dev_val).mean())
    return round(rank * 100.0, 1)


def _classify_signal(score: float | None) -> VWAPSignal:
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


def _compute_slope(vwap: pd.Series, lookback: int = _SLOPE_LOOKBACK) -> str:
    if len(vwap) < lookback + 1:
        return "flat"
    prev = float(vwap.iloc[-(lookback + 1)])
    curr = float(vwap.iloc[-1])
    if prev == 0.0:
        return "flat"
    change_pct = (curr - prev) / abs(prev) * 100.0
    if change_pct > 0.1:
        return "rising"
    if change_pct < -0.1:
        return "falling"
    return "flat"


def _build_interpretation(
    ticker: str,
    signal: VWAPSignal,
    vwap: float,
    dev_pct: float,
    score: float,
    slope: str,
) -> str:
    slope_zh = {"rising": "上升", "falling": "下降", "flat": "横盘"}.get(slope, slope)
    labels: dict[VWAPSignal, str] = {
        "strong_bull": (
            f"{ticker} 价格高于 VWAP（{vwap:.2f}），偏离 {dev_pct:+.2f}%"
            f"（百分位 {score:.0f}）：多头主导，VWAP {slope_zh}。"
        ),
        "bull": (
            f"{ticker} 价格高于 VWAP（{vwap:.2f}），偏离 {dev_pct:+.2f}%"
            f"（百分位 {score:.0f}）：价格偏强，VWAP {slope_zh}。"
        ),
        "neutral": (
            f"{ticker} 价格接近 VWAP（{vwap:.2f}），偏离 {dev_pct:+.2f}%"
            f"（百分位 {score:.0f}）：多空均衡，VWAP {slope_zh}。"
        ),
        "bear": (
            f"{ticker} 价格低于 VWAP（{vwap:.2f}），偏离 {dev_pct:+.2f}%"
            f"（百分位 {score:.0f}）：价格偏弱，VWAP {slope_zh}。"
        ),
        "strong_bear": (
            f"{ticker} 价格远低于 VWAP（{vwap:.2f}），偏离 {dev_pct:+.2f}%"
            f"（百分位 {score:.0f}）：空头主导，VWAP {slope_zh}。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 VWAP。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_vwap(ticker: str) -> VWAPData:
    """Compute rolling VWAP data for *ticker*.

    Never raises. Returns VWAPData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return VWAPData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    required = {"High", "Low", "Close", "Volume"}
    if hist.empty or not required.issubset(hist.columns):
        return VWAPData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 VWAP。",
            as_of_date=as_of,
        )

    idx = (
        hist["High"].dropna().index
        .intersection(hist["Low"].dropna().index)
        .intersection(hist["Close"].dropna().index)
        .intersection(hist["Volume"].dropna().index)
    )
    high   = hist["High"].loc[idx]
    low    = hist["Low"].loc[idx]
    close  = hist["Close"].loc[idx]
    volume = hist["Volume"].loc[idx]

    if len(close) < _MIN_BARS:
        return VWAPData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 VWAP。",
            as_of_date=as_of,
        )

    vwap_series = _compute_vwap_series(high, low, close, volume)
    dev_series  = _compute_deviation_series(close, vwap_series)

    vwap_val  = float(vwap_series.iloc[-1])
    dev_val   = float(dev_series.iloc[-1])
    above     = float(close.iloc[-1]) > vwap_val
    slope     = _compute_slope(vwap_series)

    score     = _compute_vwap_score(dev_val, dev_series)
    signal    = _classify_signal(score)
    interp    = _build_interpretation(ticker, signal, vwap_val, dev_val, score, slope)

    return VWAPData(
        ticker=ticker,
        vwap=round(vwap_val, 4),
        vwap_deviation_pct=round(dev_val, 3),
        above_vwap=above,
        vwap_slope=slope,
        vwap_score=round(score, 1),
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
