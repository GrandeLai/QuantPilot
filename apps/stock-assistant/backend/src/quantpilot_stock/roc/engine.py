"""Rate of Change (ROC) engine — Phase F.47.

ROC(n) = (Close - Close[n]) / Close[n] × 100

Default period n = 12 (≈ 2.5 weeks of trading days).

Score = percentile rank of current ROC within the last 252-bar window × 100.
  ROC at the 80th percentile of its 1-year distribution → score ≈ 80.

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

ROCSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_ROC_PERIOD = 12
_MIN_BARS = 30   # ROC period + small buffer


@dataclass
class ROCData:
    ticker: str
    roc: float | None = None             # Latest ROC (%)
    prev_roc: float | None = None        # Previous bar ROC
    roc_direction: str = ""              # "rising" | "falling" | "flat"
    roc_positive: bool = False           # ROC > 0
    roc_score: float = 50.0             # 0-100 percentile-based score
    signal: ROCSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_roc_series(close: pd.Series, period: int = _ROC_PERIOD) -> pd.Series:
    """Return ROC series (%)."""
    prev_close = close.shift(period)
    roc = ((close - prev_close) / prev_close.replace(0.0, float("nan"))) * 100.0
    return roc.fillna(0.0)


def _compute_roc_score(
    roc_val: float,
    roc_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Score = percentile rank of roc_val in last *lookback* bars of roc_series.

    Returns a value in [0, 100].
    """
    window = roc_series.iloc[-lookback:].dropna()
    if len(window) < 10:
        # Not enough history; fall back to linear mapping around 0
        return float(max(0.0, min(100.0, (roc_val + 20.0) / 40.0 * 100.0)))
    rank = float((window < roc_val).mean())  # fraction below → percentile
    return round(rank * 100.0, 1)


def _classify_signal(roc_score: float | None) -> ROCSignal:
    if roc_score is None:
        return "no_data"
    if roc_score >= 80:
        return "strong_bull"
    if roc_score >= 60:
        return "bull"
    if roc_score >= 40:
        return "neutral"
    if roc_score >= 20:
        return "bear"
    return "strong_bear"


def _build_interpretation(
    ticker: str,
    signal: ROCSignal,
    roc: float,
    roc_score: float,
) -> str:
    labels: dict[ROCSignal, str] = {
        "strong_bull": f"{ticker} ROC {roc:+.2f}%（历史第 {roc_score:.0f} 百分位）：动量极强，近期涨幅领先。",
        "bull": f"{ticker} ROC {roc:+.2f}%（历史第 {roc_score:.0f} 百分位）：动量偏强，短期价格动能正向。",
        "neutral": f"{ticker} ROC {roc:+.2f}%（历史第 {roc_score:.0f} 百分位）：动量中性，价格变动接近历史均值。",
        "bear": f"{ticker} ROC {roc:+.2f}%（历史第 {roc_score:.0f} 百分位）：动量偏弱，短期价格动能负向。",
        "strong_bear": f"{ticker} ROC {roc:+.2f}%（历史第 {roc_score:.0f} 百分位）：动量极弱，近期跌幅明显。",
        "no_data": f"{ticker} 数据不足，无法计算 ROC。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_roc(ticker: str) -> ROCData:
    """Compute ROC data for *ticker*.

    Never raises. Returns ROCData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")  # 2y for good percentile window
    except Exception:
        return ROCData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    if hist.empty or "Close" not in hist.columns:
        return ROCData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 ROC。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()

    if len(close) < _MIN_BARS:
        return ROCData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 ROC。",
            as_of_date=as_of,
        )

    roc_series = _compute_roc_series(close)

    roc_val = float(roc_series.iloc[-1])
    prev_roc = float(roc_series.iloc[-2]) if len(roc_series) >= 2 else None

    if prev_roc is not None:
        diff = roc_val - prev_roc
        if diff > 0.1:
            direction = "rising"
        elif diff < -0.1:
            direction = "falling"
        else:
            direction = "flat"
    else:
        direction = "flat"

    roc_positive = roc_val > 0.0

    roc_score = _compute_roc_score(roc_val, roc_series)
    signal = _classify_signal(roc_score)
    interpretation = _build_interpretation(ticker, signal, roc_val, roc_score)

    return ROCData(
        ticker=ticker,
        roc=round(roc_val, 3),
        prev_roc=round(prev_roc, 3) if prev_roc is not None else None,
        roc_direction=direction,
        roc_positive=roc_positive,
        roc_score=round(roc_score, 1),
        signal=signal,
        interpretation=interpretation,
        as_of_date=as_of,
        data_available=True,
    )
