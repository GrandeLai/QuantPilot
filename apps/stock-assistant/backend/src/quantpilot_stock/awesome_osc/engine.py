"""Awesome Oscillator — F.78.

Bill Williams' Awesome Oscillator (AO):
  Median Price = (High + Low) / 2
  AO = SMA(5, Median Price) − SMA(34, Median Price)

Positive AO → bullish momentum; Negative AO → bearish momentum.
Key signals: Zero-line crossover, twin peaks (divergence), saucer (continuation).

Score (0–100):
  35 pts  AO > 0 (positive momentum)
  35 pts  AO rising (current bar > previous bar)
  30 pts  percentile rank of AO in rolling 252-bar window
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

AOSignal = Literal["strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"]

_MIN_BARS = 40  # need 34 + a few bars for SMA(34)


@dataclass
class AOData:
    ticker: str
    ao_value: float | None
    ao_positive: bool | None
    ao_rising: bool | None
    ao_score: float
    signal: AOSignal
    interpretation: str
    as_of_date: str
    data_available: bool


# ---------------------------------------------------------------------------
# Core math
# ---------------------------------------------------------------------------

def _compute_ao_series(
    high: pd.Series,
    low: pd.Series,
    fast: int = 5,
    slow: int = 34,
) -> pd.Series:
    """Return AO series: SMA(fast, median) − SMA(slow, median)."""
    median = (high + low) / 2.0
    sma_fast = median.rolling(fast).mean()
    sma_slow = median.rolling(slow).mean()
    ao = (sma_fast - sma_slow).fillna(0.0)
    return ao


def _compute_ao_score(ao_series: pd.Series) -> float:
    """Composite 0–100 score."""
    score = 0.0
    ao_last = float(ao_series.iloc[-1])

    # 35 pts: AO positive
    if ao_last > 0.0:
        score += 35.0

    # 35 pts: AO rising (vs previous bar)
    if len(ao_series) >= 2:
        if ao_last > float(ao_series.iloc[-2]):
            score += 35.0

    # 30 pts: percentile of AO in rolling 252-bar window
    window = min(252, len(ao_series))
    if window >= 10:
        ao_win = ao_series.iloc[-window:]
        pct = float((ao_win < ao_last).sum()) / max(1, len(ao_win))
        score += pct * 30.0

    return round(min(100.0, max(0.0, score)), 2)


def _classify_signal(score: float | None) -> AOSignal:
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
    score: float,
    signal: AOSignal,
    ao_value: float,
    ao_positive: bool,
    ao_rising: bool,
) -> str:
    parts: list[str] = []
    sig_map = {
        "strong_bull": "极佳",
        "bull": "偏强",
        "neutral": "中性",
        "bear": "偏弱",
        "strong_bear": "极弱",
        "no_data": "数据不足",
    }
    parts.append(f"AO 综合评分 {score:.1f}/100，信号{sig_map.get(signal, signal)}。")
    parts.append(f"当前 AO 值 {ao_value:.4f}，{'正区间（多头动能）' if ao_positive else '负区间（空头动能）'}。")
    if ao_rising:
        parts.append("AO 持续走强，动能加速。")
    else:
        parts.append("AO 转弱，动能放缓。")
    parts.append("零线突破是主要信号；连续两个峰值（双峰）构成背离形态。")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def compute_ao(ticker: str) -> AOData:
    """Fetch OHLCV from yfinance and compute Awesome Oscillator."""
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period="2y")
        if df.empty or len(df) < _MIN_BARS:
            return AOData(
                ticker=ticker,
                ao_value=None,
                ao_positive=None,
                ao_rising=None,
                ao_score=0.0,
                signal="no_data",
                interpretation="数据不足，无法计算 AO。",
                as_of_date=str(date.today()),
                data_available=True,
            )

        high = df["High"].dropna()
        low = df["Low"].dropna()
        ao_series = _compute_ao_series(high, low)

        ao_last = float(ao_series.iloc[-1])
        ao_positive = ao_last > 0.0
        ao_rising = len(ao_series) >= 2 and ao_last > float(ao_series.iloc[-2])

        score = _compute_ao_score(ao_series)
        signal = _classify_signal(score)
        interp = _build_interpretation(score, signal, ao_last, ao_positive, ao_rising)

        as_of = str(df.index[-1].date()) if hasattr(df.index[-1], "date") else str(date.today())

        return AOData(
            ticker=ticker,
            ao_value=round(ao_last, 4),
            ao_positive=ao_positive,
            ao_rising=ao_rising,
            ao_score=score,
            signal=signal,
            interpretation=interp,
            as_of_date=as_of,
            data_available=True,
        )

    except Exception:
        return AOData(
            ticker=ticker,
            ao_value=None,
            ao_positive=None,
            ao_rising=None,
            ao_score=0.0,
            signal="no_data",
            interpretation="数据获取失败。",
            as_of_date=str(date.today()),
            data_available=False,
        )
