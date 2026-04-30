"""TEMA — Triple Exponential Moving Average (F.76).

Formula: TEMA(n) = 3×EMA(n) − 3×EMA(EMA(n)) + EMA(EMA(EMA(n)))
Even faster response than DEMA; reduces triple the lag of a single EMA.

Score (0–100):
  35 pts  price > TEMA  (bullish position)
  35 pts  TEMA slope positive (current vs 5-bars-ago)
  30 pts  percentile rank of (close − TEMA) / TEMA in rolling 252-bar window
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

TEMASignal = Literal["strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"]

_MIN_BARS = 45


@dataclass
class TEMAData:
    ticker: str
    tema_value: float | None
    price_above_tema: bool | None
    tema_slope_positive: bool | None
    tema_score: float
    signal: TEMASignal
    interpretation: str
    as_of_date: str
    data_available: bool


# ---------------------------------------------------------------------------
# Core math
# ---------------------------------------------------------------------------

def _compute_tema_series(close: pd.Series, period: int = 20) -> pd.Series:
    """Return TEMA series: 3×EMA − 3×EMA(EMA) + EMA(EMA(EMA))."""
    ema1 = close.ewm(span=period, adjust=False).mean()
    ema2 = ema1.ewm(span=period, adjust=False).mean()
    ema3 = ema2.ewm(span=period, adjust=False).mean()
    tema = 3.0 * ema1 - 3.0 * ema2 + ema3
    return tema.fillna(close)


def _compute_tema_score(
    close_last: float,
    tema_last: float,
    tema_series: pd.Series,
    close_series: pd.Series,
) -> float:
    """Composite 0–100 score."""
    score = 0.0

    # 35 pts: price above TEMA
    if close_last > tema_last:
        score += 35.0

    # 35 pts: TEMA slope positive
    lookback = 5
    if len(tema_series) > lookback:
        if float(tema_series.iloc[-1]) > float(tema_series.iloc[-1 - lookback]):
            score += 35.0

    # 30 pts: percentile rank of (close − TEMA)/TEMA in 252-bar window
    window = min(252, len(close_series))
    if window >= 10 and len(tema_series) == len(close_series):
        rel = (close_series - tema_series) / tema_series.replace(0.0, float("nan"))
        rel_win = rel.iloc[-window:]
        last_val = float(rel.iloc[-1]) if not pd.isna(rel.iloc[-1]) else 0.0
        pct = float((rel_win < last_val).sum()) / max(1, len(rel_win))
        score += pct * 30.0

    return round(min(100.0, max(0.0, score)), 2)


def _classify_signal(score: float | None) -> TEMASignal:
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
    signal: TEMASignal,
    price_above: bool | None,
    slope_positive: bool | None,
    period: int,
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
    parts.append(f"TEMA({period}) 综合评分 {score:.1f}/100，信号{sig_map.get(signal, signal)}。")
    if price_above is not None:
        parts.append("价格位于 TEMA 上方，趋势偏多。" if price_above else "价格位于 TEMA 下方，趋势偏空。")
    if slope_positive is not None:
        parts.append("TEMA 斜率向上，动能持续增强。" if slope_positive else "TEMA 斜率向下，动能减弱。")
    parts.append("TEMA 是三重平滑指数均线，比 DEMA 更灵敏，适用于高波动趋势市场。")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def compute_tema(ticker: str, period: int = 20) -> TEMAData:
    """Fetch OHLCV from yfinance and compute TEMA signal."""
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period="2y")
        if df.empty or len(df) < _MIN_BARS:
            return TEMAData(
                ticker=ticker,
                tema_value=None,
                price_above_tema=None,
                tema_slope_positive=None,
                tema_score=0.0,
                signal="no_data",
                interpretation="数据不足，无法计算 TEMA。",
                as_of_date=str(date.today()),
                data_available=True,
            )

        close = df["Close"].dropna()
        tema_series = _compute_tema_series(close, period)

        tema_last = float(tema_series.iloc[-1])
        close_last = float(close.iloc[-1])
        slope_positive = float(tema_series.iloc[-1]) > float(
            tema_series.iloc[-1 - min(5, len(tema_series) - 1)]
        )
        price_above = close_last > tema_last

        score = _compute_tema_score(close_last, tema_last, tema_series, close)
        signal = _classify_signal(score)
        interp = _build_interpretation(score, signal, price_above, slope_positive, period)

        as_of = str(df.index[-1].date()) if hasattr(df.index[-1], "date") else str(date.today())

        return TEMAData(
            ticker=ticker,
            tema_value=round(tema_last, 4),
            price_above_tema=price_above,
            tema_slope_positive=slope_positive,
            tema_score=score,
            signal=signal,
            interpretation=interp,
            as_of_date=as_of,
            data_available=True,
        )

    except Exception:
        return TEMAData(
            ticker=ticker,
            tema_value=None,
            price_above_tema=None,
            tema_slope_positive=None,
            tema_score=0.0,
            signal="no_data",
            interpretation="数据获取失败。",
            as_of_date=str(date.today()),
            data_available=False,
        )
