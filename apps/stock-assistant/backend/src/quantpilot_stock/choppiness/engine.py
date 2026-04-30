"""Choppiness Index — F.79.

Measures whether the market is trending or moving sideways (choppy).

Formula: CHOP(n) = 100 × log10(ΣTR(1,n) / (HH(n) − LL(n))) / log10(n)

Range: always 0–100 (by construction)
  CHOP > 61.8  → choppy / sideways / no clear trend
  38.2–61.8    → transitional
  CHOP < 38.2  → strong directional trend

Score (0–100):
  35 pts  price > SMA(20)  (directional long bias)
  35 pts  CHOP < 50        (market is in trend mode)
  30 pts  percentile of (100 − CHOP) in rolling 252-bar window
          (lower CHOP = stronger trend = higher score)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

CHOPSignal = Literal["strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"]

_MIN_BARS = 30
_CHOP_PERIOD = 14


@dataclass
class CHOPData:
    ticker: str
    chop_value: float | None
    is_trending: bool | None     # True when CHOP < 50
    price_above_sma: bool | None
    chop_score: float
    signal: CHOPSignal
    interpretation: str
    as_of_date: str
    data_available: bool


# ---------------------------------------------------------------------------
# Core math
# ---------------------------------------------------------------------------

def _compute_atr1(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """True range (1-bar ATR) without smoothing."""
    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    return tr


def _compute_chop_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Return Choppiness Index series, range 0–100."""
    tr = _compute_atr1(high, low, close)
    atr_sum = tr.rolling(period).sum()
    hh = high.rolling(period).max()
    ll = low.rolling(period).min()
    hl_range = (hh - ll).replace(0.0, float("nan"))
    chop = 100.0 * (atr_sum / hl_range).apply(
        lambda x: math.log10(x) if x > 0 else float("nan")
    ) / math.log10(period)
    return chop.clip(0.0, 100.0).ffill().fillna(50.0)


def _compute_chop_score(
    chop_last: float,
    close_last: float,
    sma_last: float,
    chop_series: pd.Series,
) -> float:
    """Composite 0–100 score."""
    score = 0.0

    # 35 pts: price above SMA(20)
    if close_last > sma_last:
        score += 35.0

    # 35 pts: CHOP < 50 (trending)
    if chop_last < 50.0:
        score += 35.0

    # 30 pts: percentile of (100 − chop) in rolling 252-bar window
    window = min(252, len(chop_series))
    if window >= 10:
        inv_chop = 100.0 - chop_series.iloc[-window:]
        last_inv = 100.0 - chop_last
        pct = float((inv_chop < last_inv).sum()) / max(1, len(inv_chop))
        score += pct * 30.0

    return round(min(100.0, max(0.0, score)), 2)


def _classify_signal(score: float | None) -> CHOPSignal:
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
    signal: CHOPSignal,
    chop_value: float,
    is_trending: bool,
    price_above_sma: bool | None,
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
    parts.append(f"Choppiness 综合评分 {score:.1f}/100，信号{sig_map.get(signal, signal)}。")
    parts.append(f"当前 CHOP 值 {chop_value:.2f}，市场处于{'趋势' if is_trending else '盘整'}状态。")
    if price_above_sma is not None:
        direction = "多头" if price_above_sma else "空头"
        parts.append(f"价格位于 SMA(20) {'上方' if price_above_sma else '下方'}，{direction}偏向。")
    parts.append("CHOP < 38.2 时趋势强烈；CHOP > 61.8 时为区间市场，趋势策略慎用。")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def compute_chop(ticker: str, period: int = _CHOP_PERIOD) -> CHOPData:
    """Fetch OHLCV from yfinance and compute Choppiness Index."""
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period="2y")
        if df.empty or len(df) < _MIN_BARS:
            return CHOPData(
                ticker=ticker,
                chop_value=None,
                is_trending=None,
                price_above_sma=None,
                chop_score=0.0,
                signal="no_data",
                interpretation="数据不足，无法计算 Choppiness Index。",
                as_of_date=str(date.today()),
                data_available=True,
            )

        high = df["High"].dropna()
        low = df["Low"].dropna()
        close = df["Close"].dropna()

        chop_series = _compute_chop_series(high, low, close, period)
        sma20 = close.rolling(20).mean().ffill().fillna(close)

        chop_last = float(chop_series.iloc[-1])
        close_last = float(close.iloc[-1])
        sma_last = float(sma20.iloc[-1])

        is_trending = chop_last < 50.0
        price_above_sma = close_last > sma_last

        score = _compute_chop_score(chop_last, close_last, sma_last, chop_series)
        signal = _classify_signal(score)
        interp = _build_interpretation(score, signal, chop_last, is_trending, price_above_sma)

        as_of = str(df.index[-1].date()) if hasattr(df.index[-1], "date") else str(date.today())

        return CHOPData(
            ticker=ticker,
            chop_value=round(chop_last, 2),
            is_trending=is_trending,
            price_above_sma=price_above_sma,
            chop_score=score,
            signal=signal,
            interpretation=interp,
            as_of_date=as_of,
            data_available=True,
        )

    except Exception:
        return CHOPData(
            ticker=ticker,
            chop_value=None,
            is_trending=None,
            price_above_sma=None,
            chop_score=0.0,
            signal="no_data",
            interpretation="数据获取失败。",
            as_of_date=str(date.today()),
            data_available=False,
        )
