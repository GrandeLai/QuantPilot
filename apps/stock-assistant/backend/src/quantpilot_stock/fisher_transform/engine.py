"""Fisher Transform — F.82.

Converts price data to a Gaussian normal distribution, generating sharp
turning-point signals at extremes.

  value  = 0.5 × ln((1 + x) / (1 - x))
  signal = prior Fisher value (1-bar lag)

  where x = 2 × [(close − lowest_low) / (highest_high − lowest_low)] − 1
        x is clamped to (−0.999, 0.999) to prevent ln() divergence

Range: unbounded; typical meaningful range −3 to +3.
  Fisher > +1.5 → overbought (potential reversal short)
  Fisher < −1.5 → oversold  (potential reversal long)
  Crossover of Fisher vs Signal line → directional trade trigger

Score (0–100):
  35 pts  Fisher > 0 (positive territory)
  35 pts  Fisher rising (vs previous bar)
  30 pts  percentile rank of Fisher in rolling 252-bar window
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

FisherSignal = Literal["strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"]

_MIN_BARS = 20  # need at least period bars for meaningful HL range


@dataclass
class FisherData:
    ticker: str
    fisher_value: float | None
    fisher_signal: float | None  # 1-bar lagged Fisher (signal line)
    fisher_score: float
    signal: FisherSignal
    interpretation: str
    as_of_date: str
    data_available: bool


# ---------------------------------------------------------------------------
# Core math
# ---------------------------------------------------------------------------

def _compute_fisher_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 10,
) -> tuple[pd.Series, pd.Series]:
    """Return (fisher, signal_line) series."""
    highest_high = high.rolling(period).max()
    lowest_low = low.rolling(period).min()

    hl_range = (highest_high - lowest_low).replace(0.0, float("nan"))

    # Normalise close to (−1, 1)
    x_raw = 2.0 * ((close - lowest_low) / hl_range) - 1.0

    # Clamp strictly inside (−1, 1) to prevent ln divergence
    x = x_raw.clip(-0.999, 0.999).fillna(0.0)

    fisher = x.apply(lambda v: 0.5 * math.log((1.0 + v) / (1.0 - v)))
    signal_line = fisher.shift(1).fillna(0.0)

    return fisher.fillna(0.0), signal_line


def _compute_fisher_score(fisher_series: pd.Series) -> float:
    """Composite 0–100 score."""
    score = 0.0
    fisher_last = float(fisher_series.iloc[-1])

    # 35 pts: Fisher > 0
    if fisher_last > 0.0:
        score += 35.0

    # 35 pts: Fisher rising vs previous bar
    if len(fisher_series) >= 2:
        if fisher_last > float(fisher_series.iloc[-2]):
            score += 35.0

    # 30 pts: percentile rank of Fisher in 252-bar window
    window = min(252, len(fisher_series))
    if window >= 10:
        fisher_win = fisher_series.iloc[-window:]
        pct = float((fisher_win < fisher_last).sum()) / max(1, len(fisher_win))
        score += pct * 30.0

    return round(min(100.0, max(0.0, score)), 2)


def _classify_signal(score: float | None) -> FisherSignal:
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
    signal: FisherSignal,
    fisher: float,
    fisher_sig: float,
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
    parts.append(f"Fisher Transform 综合评分 {score:.1f}/100，信号{sig_map.get(signal, signal)}。")
    parts.append(f"Fisher={fisher:.3f}，信号线={fisher_sig:.3f}。")
    if fisher > 1.5:
        parts.append("Fisher 超买区间（>+1.5），价格可能面临均值回归压力。")
    elif fisher < -1.5:
        parts.append("Fisher 超卖区间（<-1.5），价格可能出现反弹机会。")
    else:
        parts.append("Fisher 处于中性区间（-1.5~+1.5）。")
    if fisher > fisher_sig:
        parts.append("Fisher 上穿信号线，看多偏向。")
    elif fisher < fisher_sig:
        parts.append("Fisher 下穿信号线，看空偏向。")
    parts.append("Fisher Transform 专为捕捉价格极值反转点设计，信号前置于标准振荡器。")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def compute_fisher(ticker: str) -> FisherData:
    """Fetch OHLCV from yfinance and compute Fisher Transform."""
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period="2y")
        if df.empty or len(df) < _MIN_BARS:
            return FisherData(
                ticker=ticker,
                fisher_value=None,
                fisher_signal=None,
                fisher_score=0.0,
                signal="no_data",
                interpretation="数据不足，无法计算 Fisher Transform。",
                as_of_date=str(date.today()),
                data_available=True,
            )

        high = df["High"].dropna()
        low = df["Low"].dropna()
        close = df["Close"].dropna()

        fisher_series, signal_series = _compute_fisher_series(high, low, close)

        fisher_last = float(fisher_series.iloc[-1])
        signal_last = float(signal_series.iloc[-1])

        score = _compute_fisher_score(fisher_series)
        sig = _classify_signal(score)
        interp = _build_interpretation(score, sig, fisher_last, signal_last)

        as_of = str(df.index[-1].date()) if hasattr(df.index[-1], "date") else str(date.today())

        return FisherData(
            ticker=ticker,
            fisher_value=round(fisher_last, 4),
            fisher_signal=round(signal_last, 4),
            fisher_score=score,
            signal=sig,
            interpretation=interp,
            as_of_date=as_of,
            data_available=True,
        )

    except Exception:
        return FisherData(
            ticker=ticker,
            fisher_value=None,
            fisher_signal=None,
            fisher_score=0.0,
            signal="no_data",
            interpretation="数据获取失败。",
            as_of_date=str(date.today()),
            data_available=False,
        )
