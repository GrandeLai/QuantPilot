"""Chaikin Money Flow (CMF) engine — Phase F.43.

CMF = Sum(Money_Flow_Volume, 20) / Sum(Volume, 20)

Where:
  Money_Flow_Multiplier = ((Close - Low) - (High - Close)) / (High - Low)
  Money_Flow_Volume     = MFM × Volume

CMF ∈ [-1, 1]. Score = (CMF + 1) / 2 × 100 → [0, 100].

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import numpy as np
import pandas as pd
import yfinance as yf

CMFSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]


@dataclass
class CMFData:
    ticker: str
    cmf: float | None = None             # Latest CMF value [-1, 1]
    prev_cmf: float | None = None        # Previous bar CMF
    cmf_direction: str = ""              # "rising" | "falling" | "flat"
    cmf_positive: bool = False           # CMF > 0 (net buying pressure)
    cmf_strong_bull: bool = False        # CMF > 0.25
    cmf_strong_bear: bool = False        # CMF < -0.25
    cmf_score: float = 50.0             # 0-100 composite score
    signal: CMFSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_MIN_BARS = 25   # 20 (CMF period) + 5 (direction lookback) + guard


def _compute_cmf_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    period: int = 20,
) -> pd.Series:
    """Return CMF series in [-1, 1]."""
    hl_range = high - low

    # When high == low (doji), MFM = 0
    mfm = np.where(
        hl_range > 0,
        ((close - low) - (high - close)) / hl_range,
        0.0,
    )
    mfm_series = pd.Series(mfm, index=close.index)
    mfv = mfm_series * volume.astype(float)

    mfv_sum = mfv.rolling(period).sum()
    vol_sum = volume.astype(float).rolling(period).sum()

    # Avoid division by zero (shouldn't happen with real data, but guard anyway)
    cmf = mfv_sum / vol_sum.replace(0.0, np.nan)
    return cmf.fillna(0.0)


def _compute_cmf_score(cmf: float) -> float:
    """Map CMF [-1, 1] linearly to score [0, 100].

    score = (cmf + 1) / 2 * 100
    """
    return float(max(0.0, min(100.0, (cmf + 1.0) / 2.0 * 100.0)))


def _classify_signal(cmf_score: float | None) -> CMFSignal:
    if cmf_score is None:
        return "no_data"
    if cmf_score >= 80:
        return "strong_bull"
    if cmf_score >= 60:
        return "bull"
    if cmf_score >= 40:
        return "neutral"
    if cmf_score >= 20:
        return "bear"
    return "strong_bear"


def _build_interpretation(
    ticker: str,
    signal: CMFSignal,
    cmf: float,
    cmf_strong_bull: bool,
    cmf_strong_bear: bool,
) -> str:
    labels: dict[CMFSignal, str] = {
        "strong_bull": f"{ticker} CMF {cmf:+.3f}：资金强势流入（CMF 强正值），买盘主导。",
        "bull": f"{ticker} CMF {cmf:+.3f}：资金流入偏多（CMF 正值），买盘占优。",
        "neutral": f"{ticker} CMF {cmf:+.3f}：资金流向中性，买卖压力均衡。",
        "bear": f"{ticker} CMF {cmf:+.3f}：资金流出偏空（CMF 负值），卖盘占优。",
        "strong_bear": f"{ticker} CMF {cmf:+.3f}：资金强势流出（CMF 强负值），卖盘主导。",
        "no_data": f"{ticker} 数据不足，无法计算 CMF。",
    }
    parts = [labels.get(signal, "")]
    if cmf_strong_bull:
        parts.append("（CMF > 0.25，机构买盘明显，上涨动能强）")
    elif cmf_strong_bear:
        parts.append("（CMF < -0.25，机构卖盘明显，下行压力大）")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_cmf(ticker: str) -> CMFData:
    """Compute CMF data for *ticker*.

    Never raises. Returns CMFData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1y", interval="1d")
    except Exception:
        return CMFData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    required = {"High", "Low", "Close", "Volume"}
    if hist.empty or not required.issubset(hist.columns):
        return CMFData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 CMF。",
            as_of_date=as_of,
        )

    high = hist["High"].dropna()
    low = hist["Low"].dropna()
    close = hist["Close"].dropna()
    volume = hist["Volume"].dropna()

    common_idx = (
        high.index.intersection(low.index)
        .intersection(close.index)
        .intersection(volume.index)
    )
    high = high.loc[common_idx]
    low = low.loc[common_idx]
    close = close.loc[common_idx]
    volume = volume.loc[common_idx]

    if len(close) < _MIN_BARS:
        return CMFData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 CMF。",
            as_of_date=as_of,
        )

    cmf_series = _compute_cmf_series(high, low, close, volume)

    cmf_val = float(cmf_series.iloc[-1])
    prev_cmf = float(cmf_series.iloc[-2]) if len(cmf_series) >= 2 else None

    if prev_cmf is not None:
        diff = cmf_val - prev_cmf
        if diff > 0.005:
            direction = "rising"
        elif diff < -0.005:
            direction = "falling"
        else:
            direction = "flat"
    else:
        direction = "flat"

    cmf_positive = cmf_val > 0.0
    cmf_strong_bull = cmf_val > 0.25
    cmf_strong_bear = cmf_val < -0.25

    cmf_score = _compute_cmf_score(cmf_val)
    signal = _classify_signal(cmf_score)
    interpretation = _build_interpretation(ticker, signal, cmf_val, cmf_strong_bull, cmf_strong_bear)

    return CMFData(
        ticker=ticker,
        cmf=round(cmf_val, 4),
        prev_cmf=round(prev_cmf, 4) if prev_cmf is not None else None,
        cmf_direction=direction,
        cmf_positive=cmf_positive,
        cmf_strong_bull=cmf_strong_bull,
        cmf_strong_bear=cmf_strong_bear,
        cmf_score=round(cmf_score, 1),
        signal=signal,
        interpretation=interpretation,
        as_of_date=as_of,
        data_available=True,
    )
