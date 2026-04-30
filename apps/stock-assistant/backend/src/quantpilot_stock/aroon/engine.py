"""Aroon Indicator engine — Phase F.53.

Aroon Up   = ((n - bars since n-period high) / n) × 100
Aroon Down = ((n - bars since n-period low)  / n) × 100
Aroon Oscillator = Aroon Up - Aroon Down

Score = percentile rank of Aroon Oscillator in last 252 bars × 100.

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import numpy as np
import pandas as pd
import yfinance as yf

AroonSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_AROON_PERIOD  = 25
_MIN_BARS      = _AROON_PERIOD + 10   # need at least period + buffer


@dataclass
class AroonData:
    ticker: str
    aroon_up: float | None = None          # 0–100
    aroon_down: float | None = None        # 0–100
    aroon_oscillator: float | None = None  # -100 to +100
    aroon_bullish: bool = False            # oscillator > 0
    aroon_score: float = 50.0             # 0–100 percentile
    signal: AroonSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_aroon_series(
    high: pd.Series,
    low: pd.Series,
    period: int = _AROON_PERIOD,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Return (aroon_up, aroon_down, aroon_oscillator) series."""
    n = len(high)
    up_vals   = np.full(n, float("nan"))
    down_vals = np.full(n, float("nan"))

    for i in range(period, n):
        window_high = high.iloc[i - period : i + 1].values
        window_low  = low.iloc[i - period : i + 1].values
        # argmax/argmin gives index within window; 0 = oldest, period = newest
        bars_since_high = period - int(np.argmax(window_high))
        bars_since_low  = period - int(np.argmin(window_low))
        up_vals[i]   = (period - bars_since_high) / period * 100.0
        down_vals[i] = (period - bars_since_low)  / period * 100.0

    idx   = high.index
    up    = pd.Series(up_vals,   index=idx)
    down  = pd.Series(down_vals, index=idx)
    osc   = up - down
    return up, down, osc


def _compute_aroon_score(
    osc_val: float,
    osc_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Percentile rank of osc_val within last *lookback* bars × 100."""
    window = osc_series.iloc[-lookback:].dropna()
    if len(window) < 10:
        # fallback: map [-100, +100] → [0, 100]
        return float(max(0.0, min(100.0, (osc_val + 100.0) / 200.0 * 100.0)))
    rank = float((window < osc_val).mean())
    return round(rank * 100.0, 1)


def _classify_signal(score: float | None) -> AroonSignal:
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
    signal: AroonSignal,
    up: float,
    down: float,
    osc: float,
    score: float,
    bullish: bool,
) -> str:
    trend = "上升趋势" if bullish else "下降趋势"
    labels: dict[AroonSignal, str] = {
        "strong_bull": (
            f"{ticker} Aroon Up={up:.0f}，Down={down:.0f}，振荡器={osc:+.0f}"
            f"（百分位 {score:.0f}）：{trend}极强，高位突破信号。"
        ),
        "bull": (
            f"{ticker} Aroon Up={up:.0f}，Down={down:.0f}，振荡器={osc:+.0f}"
            f"（百分位 {score:.0f}）：{trend}偏强，看涨动能占优。"
        ),
        "neutral": (
            f"{ticker} Aroon Up={up:.0f}，Down={down:.0f}，振荡器={osc:+.0f}"
            f"（百分位 {score:.0f}）：多空势均力敌，趋势方向不明。"
        ),
        "bear": (
            f"{ticker} Aroon Up={up:.0f}，Down={down:.0f}，振荡器={osc:+.0f}"
            f"（百分位 {score:.0f}）：{trend}偏弱，看跌动能占优。"
        ),
        "strong_bear": (
            f"{ticker} Aroon Up={up:.0f}，Down={down:.0f}，振荡器={osc:+.0f}"
            f"（百分位 {score:.0f}）：{trend}极强，低位跌破信号。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 Aroon。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_aroon(ticker: str) -> AroonData:
    """Compute Aroon Indicator for *ticker*.

    Never raises. Returns AroonData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return AroonData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    if hist.empty or "High" not in hist.columns or "Low" not in hist.columns:
        return AroonData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 Aroon。",
            as_of_date=as_of,
        )

    high  = hist["High"].dropna()
    low   = hist["Low"].dropna()
    close = hist["Close"].dropna()

    # Align to common index
    common_idx = high.index.intersection(low.index).intersection(close.index)
    high  = high.loc[common_idx]
    low   = low.loc[common_idx]

    if len(high) < _MIN_BARS:
        return AroonData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 Aroon。",
            as_of_date=as_of,
        )

    up_series, down_series, osc_series = _compute_aroon_series(high, low)

    up_val  = float(up_series.iloc[-1])
    dn_val  = float(down_series.iloc[-1])
    osc_val = float(osc_series.iloc[-1])
    bullish = osc_val > 0.0

    score  = _compute_aroon_score(osc_val, osc_series)
    signal = _classify_signal(score)
    interp = _build_interpretation(ticker, signal, up_val, dn_val, osc_val, score, bullish)

    return AroonData(
        ticker=ticker,
        aroon_up=round(up_val, 1),
        aroon_down=round(dn_val, 1),
        aroon_oscillator=round(osc_val, 1),
        aroon_bullish=bullish,
        aroon_score=round(score, 1),
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
