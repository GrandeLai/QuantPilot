"""Pivot Points — F.85.

Classic pivot points calculated from the previous session's High, Low, Close.
Widely used for intraday and swing support/resistance reference levels.

  PP  = (High + Low + Close) / 3
  R1  = 2×PP − Low
  S1  = 2×PP − High
  R2  = PP + (High − Low)
  S2  = PP − (High − Low)
  R3  = High + 2×(PP − Low)
  S3  = Low  − 2×(High − PP)

Score (0–100):
  Based on where today's close sits relative to pivot levels:
  50 pts  Close > PP (above pivot = bullish bias)
  20 pts  Close > R1 (above first resistance)
  10 pts  Close > R2 (above second resistance)
  Or:
  −20 pts  Close < S1
  −10 pts  Close < S2
  (Score floored at 0, capped at 100; converted to 0-100 scale)

Simplified scoring for composite:
  35 pts  Close > PP
  35 pts  Close > prior session close (positive momentum)
  30 pts  percentile rank of (close − PP) / PP in rolling 252-bar window
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

PivotSignal = Literal["strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"]

_MIN_BARS = 5  # just need prior session


@dataclass
class PivotData:
    """Pivot point levels, score, signal, and availability metadata."""

    ticker: str
    pp: float | None       # Pivot Point
    r1: float | None
    r2: float | None
    r3: float | None
    s1: float | None
    s2: float | None
    s3: float | None
    close: float | None    # latest close
    pivot_score: float
    signal: PivotSignal
    interpretation: str
    as_of_date: str
    data_available: bool


# ---------------------------------------------------------------------------
# Core math
# ---------------------------------------------------------------------------

def _compute_pivot_levels(
    high: float, low: float, close_prev: float,
) -> tuple[float, float, float, float, float, float, float]:
    """Return (PP, R1, R2, R3, S1, S2, S3)."""
    pp = (high + low + close_prev) / 3.0
    r1 = 2.0 * pp - low
    s1 = 2.0 * pp - high
    r2 = pp + (high - low)
    s2 = pp - (high - low)
    r3 = high + 2.0 * (pp - low)
    s3 = low - 2.0 * (high - pp)
    return pp, r1, r2, r3, s1, s2, s3


def _compute_pivot_score_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
) -> tuple[pd.Series, float, float, float, float, float, float, float]:
    """Compute PP and S/R levels from prior session, return score series + last levels."""
    # Use prior session's H/L/C
    h_prev = high.shift(1)
    l_prev = low.shift(1)
    c_prev = close.shift(1)

    pp = (h_prev + l_prev + c_prev) / 3.0

    # Relative distance of close from PP, normalised by PP
    rel = (close - pp) / pp.replace(0.0, float("nan"))
    rel_filled = rel.fillna(0.0)

    # Latest levels
    last_h = float(high.iloc[-2]) if len(high) >= 2 else float(high.iloc[-1])
    last_l = float(low.iloc[-2]) if len(low) >= 2 else float(low.iloc[-1])
    last_c_prev = float(close.iloc[-2]) if len(close) >= 2 else float(close.iloc[-1])
    pp_last, r1_last, r2_last, r3_last, s1_last, s2_last, s3_last = _compute_pivot_levels(
        last_h, last_l, last_c_prev
    )

    return rel_filled, pp_last, r1_last, r2_last, r3_last, s1_last, s2_last, s3_last


def _compute_pivot_score(
    close: pd.Series,
    pp_series: pd.Series,
) -> float:
    """Composite 0–100 score."""
    score = 0.0
    close_last = float(close.iloc[-1])
    pp_last = float(pp_series.iloc[-1])

    # 35 pts: Close > PP
    if close_last > pp_last:
        score += 35.0

    # 35 pts: Close rising vs prior session
    if len(close) >= 2:
        if close_last > float(close.iloc[-2]):
            score += 35.0

    # 30 pts: percentile rank of (close - PP) relative to 252-bar history
    rel = (close - pp_series) / pp_series.replace(0.0, float("nan"))
    rel = rel.fillna(0.0)
    window = min(252, len(rel))
    if window >= 10:
        rel_win = rel.iloc[-window:]
        rel_last = float(rel.iloc[-1])
        pct = float((rel_win < rel_last).sum()) / max(1, len(rel_win))
        score += pct * 30.0

    return round(min(100.0, max(0.0, score)), 2)


def _classify_signal(score: float | None) -> PivotSignal:
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
    signal: PivotSignal,
    pp: float,
    r1: float,
    r2: float,
    s1: float,
    s2: float,
    close_val: float,
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
    parts.append(f"Pivot Points 综合评分 {score:.1f}/100，信号{sig_map.get(signal, signal)}。")
    parts.append(f"PP={pp:.2f}，R1={r1:.2f}，R2={r2:.2f}，S1={s1:.2f}，S2={s2:.2f}，收盘={close_val:.2f}。")
    if close_val >= r2:
        parts.append("收盘价突破 R2，强势多头。")
    elif close_val >= r1:
        parts.append("收盘价位于 R1 至 R2 之间，多头偏强，注意 R2 压力。")
    elif close_val >= pp:
        parts.append("收盘价位于 PP 至 R1 之间，多头偏向，关注 R1 突破。")
    elif close_val >= s1:
        parts.append("收盘价位于 S1 至 PP 之间，空头偏向，关注 S1 支撑。")
    elif close_val >= s2:
        parts.append("收盘价跌破 S1，空头偏弱，注意 S2 支撑。")
    else:
        parts.append("收盘价跌破 S2，弱势空头格局。")
    parts.append("Pivot Points 是传统技术分析最常用的支撑压力参考，适合盘中止盈止损设置。")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def compute_pivot_points(ticker: str) -> PivotData:
    """Fetch OHLCV from yfinance and compute Pivot Points."""
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period="2y")
        if df.empty or len(df) < _MIN_BARS:
            return PivotData(
                ticker=ticker,
                pp=None, r1=None, r2=None, r3=None,
                s1=None, s2=None, s3=None,
                close=None,
                pivot_score=0.0,
                signal="no_data",
                interpretation="数据不足，无法计算 Pivot Points。",
                as_of_date=str(date.today()),
                data_available=True,
            )

        high = df["High"].dropna()
        low = df["Low"].dropna()
        close = df["Close"].dropna()

        # Compute pivot from prior session
        h_prev = float(high.iloc[-2])
        l_prev = float(low.iloc[-2])
        c_prev = float(close.iloc[-2])
        close_last = float(close.iloc[-1])

        pp, r1, r2, r3, s1, s2, s3 = _compute_pivot_levels(h_prev, l_prev, c_prev)

        # Build PP series for score computation
        h_shift = high.shift(1).fillna(high)
        l_shift = low.shift(1).fillna(low)
        c_shift = close.shift(1).fillna(close)
        pp_series = (h_shift + l_shift + c_shift) / 3.0

        score = _compute_pivot_score(close, pp_series)
        sig = _classify_signal(score)
        interp = _build_interpretation(score, sig, pp, r1, r2, s1, s2, close_last)

        as_of = str(df.index[-1].date()) if hasattr(df.index[-1], "date") else str(date.today())

        return PivotData(
            ticker=ticker,
            pp=round(pp, 4),
            r1=round(r1, 4),
            r2=round(r2, 4),
            r3=round(r3, 4),
            s1=round(s1, 4),
            s2=round(s2, 4),
            s3=round(s3, 4),
            close=round(close_last, 4),
            pivot_score=score,
            signal=sig,
            interpretation=interp,
            as_of_date=as_of,
            data_available=True,
        )

    except Exception:
        return PivotData(
            ticker=ticker,
            pp=None, r1=None, r2=None, r3=None,
            s1=None, s2=None, s3=None,
            close=None,
            pivot_score=0.0,
            signal="no_data",
            interpretation="数据获取失败。",
            as_of_date=str(date.today()),
            data_available=False,
        )
