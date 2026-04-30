"""Force Index engine — Phase F.51.

Elder's Force Index:
  Raw FI(t) = (Close(t) − Close(t−1)) × Volume(t)
  Smoothed FI = EMA(Raw FI, 13)

Score = percentile rank of smoothed FI within last 252 bars × 100.
  Positive (bullish force) → higher rank.

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

ForceIndexSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_FI_EMA_PERIOD = 13
_MIN_BARS = 30


@dataclass
class ForceIndexData:
    ticker: str
    force_index: float | None = None         # Smoothed EMA(13) force index
    fi_positive: bool = False                # FI > 0
    fi_direction: str = ""                   # "rising" | "falling" | "flat"
    fi_normalized: float | None = None       # FI / (price × avg_vol) × 100
    fi_score: float = 50.0                  # 0-100 percentile-based score
    signal: ForceIndexSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_fi_series(
    close: pd.Series,
    volume: pd.Series,
    ema_period: int = _FI_EMA_PERIOD,
) -> pd.Series:
    """Return smoothed Force Index series (EMA of raw FI)."""
    raw_fi = close.diff() * volume.astype(float)
    smoothed = raw_fi.ewm(span=ema_period, adjust=False).mean()
    return smoothed.fillna(0.0)


def _compute_fi_score(
    fi_val: float,
    fi_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Percentile rank of fi_val within last *lookback* bars × 100."""
    window = fi_series.iloc[-lookback:].dropna()
    if len(window) < 10:
        # Fallback: symmetric around 0, ±1 stdev → [0, 100]
        std = float(window.std()) if len(window) > 1 else 1.0
        if std == 0.0:
            std = 1.0
        return float(max(0.0, min(100.0, (fi_val / std / 4.0 + 0.5) * 100.0)))
    rank = float((window < fi_val).mean())
    return round(rank * 100.0, 1)


def _classify_signal(score: float | None) -> ForceIndexSignal:
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


def _compute_fi_direction(fi_series: pd.Series) -> str:
    if len(fi_series) < 2:
        return "flat"
    curr = float(fi_series.iloc[-1])
    prev = float(fi_series.iloc[-2])
    diff = curr - prev
    if diff > abs(curr) * 0.01:
        return "rising"
    if diff < -abs(curr) * 0.01:
        return "falling"
    return "flat"


def _compute_fi_normalized(
    fi_val: float,
    close_val: float,
    volume_series: pd.Series,
    lookback: int = 20,
) -> float | None:
    """FI / (price × avg_volume) × 100 — scale-independent metric."""
    if close_val == 0.0:
        return None
    avg_vol = float(volume_series.iloc[-lookback:].mean())
    if avg_vol == 0.0:
        return None
    return round(fi_val / (close_val * avg_vol) * 100.0, 4)


def _build_interpretation(
    ticker: str,
    signal: ForceIndexSignal,
    fi: float,
    score: float,
    direction: str,
) -> str:
    dir_zh = {"rising": "增强", "falling": "减弱", "flat": "持平"}.get(direction, direction)
    sign_str = "正（看涨）" if fi >= 0 else "负（看跌）"
    labels: dict[ForceIndexSignal, str] = {
        "strong_bull": (
            f"{ticker} 力量指数 {fi:.0f}（{sign_str}，百分位 {score:.0f}），力量{dir_zh}：动能极强，多方主导。"
        ),
        "bull": (
            f"{ticker} 力量指数 {fi:.0f}（{sign_str}，百分位 {score:.0f}），力量{dir_zh}：多方偏强。"
        ),
        "neutral": (
            f"{ticker} 力量指数 {fi:.0f}（{sign_str}，百分位 {score:.0f}），力量{dir_zh}：多空均衡。"
        ),
        "bear": (
            f"{ticker} 力量指数 {fi:.0f}（{sign_str}，百分位 {score:.0f}），力量{dir_zh}：空方偏强。"
        ),
        "strong_bear": (
            f"{ticker} 力量指数 {fi:.0f}（{sign_str}，百分位 {score:.0f}），力量{dir_zh}：动能极弱，空方主导。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算力量指数。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_force_index(ticker: str) -> ForceIndexData:
    """Compute Force Index data for *ticker*.

    Never raises. Returns ForceIndexData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return ForceIndexData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    required = {"Close", "Volume"}
    if hist.empty or not required.issubset(hist.columns):
        return ForceIndexData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算力量指数。",
            as_of_date=as_of,
        )

    close  = hist["Close"].dropna()
    volume = hist["Volume"].dropna()
    idx    = close.index.intersection(volume.index)
    close, volume = close.loc[idx], volume.loc[idx]

    if len(close) < _MIN_BARS:
        return ForceIndexData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算力量指数。",
            as_of_date=as_of,
        )

    fi_series  = _compute_fi_series(close, volume)
    fi_val     = float(fi_series.iloc[-1])
    fi_positive = fi_val > 0.0
    direction  = _compute_fi_direction(fi_series)
    fi_norm    = _compute_fi_normalized(fi_val, float(close.iloc[-1]), volume)

    score      = _compute_fi_score(fi_val, fi_series)
    signal     = _classify_signal(score)
    interp     = _build_interpretation(ticker, signal, fi_val, score, direction)

    return ForceIndexData(
        ticker=ticker,
        force_index=round(fi_val, 2),
        fi_positive=fi_positive,
        fi_direction=direction,
        fi_normalized=fi_norm,
        fi_score=round(score, 1),
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
