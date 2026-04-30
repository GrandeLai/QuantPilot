"""Donchian Channels engine — Phase F.58.

Upper   = max(High, n)
Lower   = min(Low,  n)
Middle  = (Upper + Lower) / 2
Position = (Close − Lower) / (Upper − Lower) × 100   [0–100]

Score = percentile rank of Position in last 252 bars × 100.

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

DonchianSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_PERIOD   = 20
_MIN_BARS = _PERIOD + 5


@dataclass
class DonchianData:
    ticker: str
    upper: float | None = None               # Upper band price
    lower: float | None = None               # Lower band price
    middle: float | None = None              # Mid-channel price
    position: float | None = None           # 0–100 channel position
    channel_width_pct: float | None = None  # (Upper−Lower)/Middle × 100
    donchian_score: float = 50.0           # 0–100 percentile of position
    signal: DonchianSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_donchian_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = _PERIOD,
) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """Return (upper, lower, middle, position) series."""
    upper  = high.rolling(period).max()
    lower  = low.rolling(period).min()
    middle = (upper + lower) / 2.0
    width  = (upper - lower).replace(0.0, float("nan"))
    pos    = ((close - lower) / width * 100.0).clip(0.0, 100.0).fillna(50.0)
    return upper, lower, middle, pos


def _compute_donchian_score(
    pos_val: float,
    pos_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Percentile rank of pos_val in last *lookback* bars × 100."""
    window = pos_series.iloc[-lookback:].dropna()
    if len(window) < 10:
        return float(max(0.0, min(100.0, pos_val)))
    rank = float((window < pos_val).mean())
    return round(rank * 100.0, 1)


def _classify_signal(score: float | None) -> DonchianSignal:
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
    signal: DonchianSignal,
    upper: float,
    lower: float,
    pos: float,
    score: float,
    width_pct: float,
) -> str:
    labels: dict[DonchianSignal, str] = {
        "strong_bull": (
            f"{ticker} 价格位于通道上方 {pos:.0f}%（百分位 {score:.0f}），"
            f"通道宽度 {width_pct:.1f}%：强势突破上轨，动量极强。"
        ),
        "bull": (
            f"{ticker} 价格位于通道上方 {pos:.0f}%（百分位 {score:.0f}），"
            f"通道宽度 {width_pct:.1f}%：价格偏强，看涨倾向。"
        ),
        "neutral": (
            f"{ticker} 价格位于通道中间 {pos:.0f}%（百分位 {score:.0f}），"
            f"通道宽度 {width_pct:.1f}%：价格在通道中性区间。"
        ),
        "bear": (
            f"{ticker} 价格位于通道下方 {pos:.0f}%（百分位 {score:.0f}），"
            f"通道宽度 {width_pct:.1f}%：价格偏弱，看跌倾向。"
        ),
        "strong_bear": (
            f"{ticker} 价格位于通道下方 {pos:.0f}%（百分位 {score:.0f}），"
            f"通道宽度 {width_pct:.1f}%：跌破下轨，趋势极弱。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 Donchian 通道。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_donchian(ticker: str) -> DonchianData:
    """Compute Donchian Channels for *ticker*.

    Never raises. Returns DonchianData with data_available=False on failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return DonchianData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    required = {"High", "Low", "Close"}
    if hist.empty or not required.issubset(hist.columns):
        return DonchianData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 Donchian 通道。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()
    high  = hist["High"].loc[close.index].dropna()
    low   = hist["Low"].loc[close.index].dropna()

    common = close.index.intersection(high.index).intersection(low.index)
    close, high, low = close.loc[common], high.loc[common], low.loc[common]

    if len(close) < _MIN_BARS:
        return DonchianData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 Donchian 通道。",
            as_of_date=as_of,
        )

    upper_s, lower_s, mid_s, pos_s = _compute_donchian_series(high, low, close)

    upper_val  = float(upper_s.iloc[-1])
    lower_val  = float(lower_s.iloc[-1])
    mid_val    = float(mid_s.iloc[-1])
    pos_val    = float(pos_s.iloc[-1])

    width_pct  = (upper_val - lower_val) / mid_val * 100.0 if mid_val != 0 else 0.0

    score  = _compute_donchian_score(pos_val, pos_s)
    signal = _classify_signal(score)
    interp = _build_interpretation(ticker, signal, upper_val, lower_val, pos_val, score, width_pct)

    return DonchianData(
        ticker=ticker,
        upper=round(upper_val, 4),
        lower=round(lower_val, 4),
        middle=round(mid_val, 4),
        position=round(pos_val, 1),
        channel_width_pct=round(width_pct, 2),
        donchian_score=round(score, 1),
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
