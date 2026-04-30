"""Connors RSI (CRSI) — F.81.

Three-component composite momentum oscillator developed by Larry Connors:

  CRSI(3,2,100) = [RSI(3) + RSI(streak, 2) + PercentRank(ROC(1), 100)] / 3

  1. RSI(3)         — very short-term RSI for momentum sensitivity
  2. Streak RSI     — count consecutive up/down days, then compute RSI(2) of the count
  3. PercentRank    — percentile rank of today's 1-bar ROC over the past 100 bars

Range: 0–100
  CRSI > 70 → overbought  (mean-reversion short opportunity)
  CRSI < 30 → oversold    (mean-reversion long opportunity)

Score (0–100):
  35 pts  CRSI > 50 (positive momentum)
  35 pts  CRSI rising (vs previous bar)
  30 pts  percentile rank of CRSI in rolling 252-bar window
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

CRSISignal = Literal["strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"]

_MIN_BARS = 110  # need 100 bars for PercentRank + warm-up


@dataclass
class CRSIData:
    ticker: str
    crsi_value: float | None
    rsi3: float | None
    streak_rsi: float | None
    percent_rank: float | None
    crsi_score: float
    signal: CRSISignal
    interpretation: str
    as_of_date: str
    data_available: bool


# ---------------------------------------------------------------------------
# Core math
# ---------------------------------------------------------------------------

def _compute_rsi(series: pd.Series, period: int) -> pd.Series:
    """Standard Wilder RSI. When avg_loss=0 → RSI=100; when avg_gain=0 → RSI=0."""
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
    # Avoid divide-by-zero: use tiny floor; RSI→100 when loss≈0
    rs = avg_gain / avg_loss.clip(lower=1e-10)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0).clip(0.0, 100.0)


def _compute_streak(close: pd.Series) -> pd.Series:
    """Consecutive up (+) / down (-) day count."""
    changes = close.diff()
    streaks = []
    current = 0
    for chg in changes:
        if pd.isna(chg) or chg == 0.0:
            current = 0
            streaks.append(0)
        elif chg > 0:
            current = current + 1 if current > 0 else 1
            streaks.append(current)
        else:
            current = current - 1 if current < 0 else -1
            streaks.append(current)
    return pd.Series(streaks, index=close.index, dtype=float)


def _compute_percent_rank(roc1: pd.Series, lookback: int = 100) -> pd.Series:
    """Rolling percentile rank (0–100) of today's ROC over past N bars."""
    def _rank(x: pd.Series) -> float:
        return float((x.iloc[:-1] < x.iloc[-1]).sum()) / max(1, len(x) - 1) * 100.0

    return roc1.rolling(lookback + 1).apply(_rank, raw=False).fillna(50.0)


def _compute_crsi_series(
    close: pd.Series,
    rsi_period: int = 3,
    streak_period: int = 2,
    rank_period: int = 100,
) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """Return (crsi, rsi3, streak_rsi, percent_rank) series."""
    rsi3 = _compute_rsi(close, rsi_period)
    streak = _compute_streak(close)
    streak_rsi = _compute_rsi(streak, streak_period)
    roc1 = close.pct_change(1).fillna(0.0) * 100.0
    prank = _compute_percent_rank(roc1, rank_period)
    crsi = ((rsi3 + streak_rsi + prank) / 3.0).clip(0.0, 100.0)
    return crsi, rsi3, streak_rsi, prank


def _compute_crsi_score(crsi_series: pd.Series) -> float:
    """Composite 0–100 score."""
    score = 0.0
    crsi_last = float(crsi_series.iloc[-1])

    # 35 pts: CRSI > 50
    if crsi_last > 50.0:
        score += 35.0

    # 35 pts: CRSI rising vs previous bar
    if len(crsi_series) >= 2:
        if crsi_last > float(crsi_series.iloc[-2]):
            score += 35.0

    # 30 pts: percentile rank of CRSI in 252-bar window
    window = min(252, len(crsi_series))
    if window >= 10:
        crsi_win = crsi_series.iloc[-window:]
        pct = float((crsi_win < crsi_last).sum()) / max(1, len(crsi_win))
        score += pct * 30.0

    return round(min(100.0, max(0.0, score)), 2)


def _classify_signal(score: float | None) -> CRSISignal:
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
    signal: CRSISignal,
    crsi: float,
    rsi3: float,
    streak_rsi: float,
    prank: float,
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
    parts.append(f"Connors RSI 综合评分 {score:.1f}/100，信号{sig_map.get(signal, signal)}。")
    parts.append(f"CRSI={crsi:.1f}，RSI(3)={rsi3:.1f}，连涨跌RSI={streak_rsi:.1f}，百分位={prank:.1f}。")
    if crsi > 70:
        parts.append("CRSI 超买区间（>70），适合均值回归短线轻仓做空或平多。")
    elif crsi < 30:
        parts.append("CRSI 超卖区间（<30），适合均值回归短线轻仓做多。")
    else:
        parts.append("CRSI 处于中性区间，动量无明显极值。")
    parts.append("Connors RSI 专为短期均值回归策略设计，配合支撑压力位使用效果更佳。")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def compute_crsi(ticker: str) -> CRSIData:
    """Fetch OHLCV from yfinance and compute Connors RSI."""
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period="2y")
        if df.empty or len(df) < _MIN_BARS:
            return CRSIData(
                ticker=ticker,
                crsi_value=None,
                rsi3=None,
                streak_rsi=None,
                percent_rank=None,
                crsi_score=0.0,
                signal="no_data",
                interpretation="数据不足，无法计算 Connors RSI。",
                as_of_date=str(date.today()),
                data_available=True,
            )

        close = df["Close"].dropna()
        crsi_series, rsi3_series, srsi_series, prank_series = _compute_crsi_series(close)

        crsi_last = float(crsi_series.iloc[-1])
        rsi3_last = float(rsi3_series.iloc[-1])
        srsi_last = float(srsi_series.iloc[-1])
        prank_last = float(prank_series.iloc[-1])

        score = _compute_crsi_score(crsi_series)
        signal = _classify_signal(score)
        interp = _build_interpretation(score, signal, crsi_last, rsi3_last, srsi_last, prank_last)

        as_of = str(df.index[-1].date()) if hasattr(df.index[-1], "date") else str(date.today())

        return CRSIData(
            ticker=ticker,
            crsi_value=round(crsi_last, 2),
            rsi3=round(rsi3_last, 2),
            streak_rsi=round(srsi_last, 2),
            percent_rank=round(prank_last, 2),
            crsi_score=score,
            signal=signal,
            interpretation=interp,
            as_of_date=as_of,
            data_available=True,
        )

    except Exception:
        return CRSIData(
            ticker=ticker,
            crsi_value=None,
            rsi3=None,
            streak_rsi=None,
            percent_rank=None,
            crsi_score=0.0,
            signal="no_data",
            interpretation="数据获取失败。",
            as_of_date=str(date.today()),
            data_available=False,
        )
