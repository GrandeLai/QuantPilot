"""Commodity Channel Index (CCI) engine — Phase F.45.

CCI = (TP - SMA(TP, n)) / (0.015 × MeanAbsoluteDeviation(TP, n))

Typical Price (TP) = (High + Low + Close) / 3

  CCI > +100  → overbought / strong bull momentum
  CCI > 0     → mild bull
  CCI < -100  → oversold / strong bear momentum
  CCI < 0     → mild bear

Score = clip((CCI + 200) / 400 × 100, 0, 100)
  CCI=+200 → score=100; CCI=0 → score=50; CCI=-200 → score=0

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

CCISignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]


@dataclass
class CCIData:
    ticker: str
    cci: float | None = None             # Latest CCI value
    prev_cci: float | None = None        # Previous bar CCI
    cci_direction: str = ""              # "rising" | "falling" | "flat"
    overbought: bool = False             # CCI > 100
    oversold: bool = False               # CCI < -100
    cci_score: float = 50.0             # 0-100 composite score
    signal: CCISignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_MIN_BARS = 25   # 20 (CCI period) + 5 guard


def _compute_cci_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 20,
) -> pd.Series:
    """Return CCI series."""
    tp = (high + low + close) / 3.0

    sma_tp = tp.rolling(period).mean()

    # Mean absolute deviation: average of |TP_i - SMA_TP| over period
    def mad(x: pd.Series) -> float:
        return float((x - x.mean()).abs().mean())

    mean_dev = tp.rolling(period).apply(mad, raw=False)

    # Avoid division by zero
    cci = (tp - sma_tp) / (0.015 * mean_dev.replace(0.0, float("nan")))
    return cci.fillna(0.0)


def _compute_cci_score(cci: float) -> float:
    """Map CCI to [0, 100].

    Design: CCI=+200 → 100, CCI=0 → 50, CCI=-200 → 0.
    """
    return float(max(0.0, min(100.0, (cci + 200.0) / 400.0 * 100.0)))


def _classify_signal(cci_score: float | None) -> CCISignal:
    if cci_score is None:
        return "no_data"
    if cci_score >= 80:
        return "strong_bull"
    if cci_score >= 60:
        return "bull"
    if cci_score >= 40:
        return "neutral"
    if cci_score >= 20:
        return "bear"
    return "strong_bear"


def _build_interpretation(
    ticker: str,
    signal: CCISignal,
    cci: float,
    overbought: bool,
    oversold: bool,
) -> str:
    labels: dict[CCISignal, str] = {
        "strong_bull": f"{ticker} CCI {cci:.1f}：价格大幅偏离均值上方，强势多头动能。",
        "bull": f"{ticker} CCI {cci:.1f}：价格偏离均值向上，买盘占优。",
        "neutral": f"{ticker} CCI {cci:.1f}：价格接近均值，多空均衡。",
        "bear": f"{ticker} CCI {cci:.1f}：价格偏离均值向下，卖盘占优。",
        "strong_bear": f"{ticker} CCI {cci:.1f}：价格大幅偏离均值下方，强势空头动能。",
        "no_data": f"{ticker} 数据不足，无法计算 CCI。",
    }
    parts = [labels.get(signal, "")]
    if overbought:
        parts.append("（CCI > 100，超买区，注意回调风险）")
    elif oversold:
        parts.append("（CCI < -100，超卖区，关注反弹机会）")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_cci(ticker: str) -> CCIData:
    """Compute CCI data for *ticker*.

    Never raises. Returns CCIData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1y", interval="1d")
    except Exception:
        return CCIData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    required = {"High", "Low", "Close"}
    if hist.empty or not required.issubset(hist.columns):
        return CCIData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 CCI。",
            as_of_date=as_of,
        )

    high = hist["High"].dropna()
    low = hist["Low"].dropna()
    close = hist["Close"].dropna()

    common_idx = high.index.intersection(low.index).intersection(close.index)
    high = high.loc[common_idx]
    low = low.loc[common_idx]
    close = close.loc[common_idx]

    if len(close) < _MIN_BARS:
        return CCIData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 CCI。",
            as_of_date=as_of,
        )

    cci_series = _compute_cci_series(high, low, close)

    cci_val = float(cci_series.iloc[-1])
    prev_cci = float(cci_series.iloc[-2]) if len(cci_series) >= 2 else None

    if prev_cci is not None:
        diff = cci_val - prev_cci
        if diff > 2.0:
            direction = "rising"
        elif diff < -2.0:
            direction = "falling"
        else:
            direction = "flat"
    else:
        direction = "flat"

    overbought = cci_val > 100.0
    oversold = cci_val < -100.0

    cci_score = _compute_cci_score(cci_val)
    signal = _classify_signal(cci_score)
    interpretation = _build_interpretation(ticker, signal, cci_val, overbought, oversold)

    return CCIData(
        ticker=ticker,
        cci=round(cci_val, 2),
        prev_cci=round(prev_cci, 2) if prev_cci is not None else None,
        cci_direction=direction,
        overbought=overbought,
        oversold=oversold,
        cci_score=round(cci_score, 1),
        signal=signal,
        interpretation=interpretation,
        as_of_date=as_of,
        data_available=True,
    )
