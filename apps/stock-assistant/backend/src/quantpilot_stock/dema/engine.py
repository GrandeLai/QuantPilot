"""DEMA — Double Exponential Moving Average (F.75).

Formula: DEMA(n) = 2 × EMA(n) - EMA(EMA(n))
Eliminates the lag inherent in a single EMA by subtracting the double-smoothed EMA.

Score (0–100):
  35 pts  price > DEMA  (bullish position)
  35 pts  DEMA slope positive (current vs 5-bars-ago)
  30 pts  percentile rank of (close − DEMA) / DEMA in rolling 252-bar window
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

DEMASignal = Literal["strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"]

_MIN_BARS = 40  # need enough bars for EMA(EMA) to converge


@dataclass
class DEMAData:
    ticker: str
    dema_value: float | None
    price_above_dema: bool | None
    dema_slope_positive: bool | None
    dema_score: float
    signal: DEMASignal
    interpretation: str
    as_of_date: str
    data_available: bool


# ---------------------------------------------------------------------------
# Core math
# ---------------------------------------------------------------------------

def _compute_dema_series(close: pd.Series, period: int = 20) -> pd.Series:
    """Return DEMA series: 2×EMA(n) − EMA(EMA(n))."""
    ema1 = close.ewm(span=period, adjust=False).mean()
    ema2 = ema1.ewm(span=period, adjust=False).mean()
    dema = 2.0 * ema1 - ema2
    return dema.fillna(close)


def _compute_dema_score(
    cv: float,
    close_last: float,
    dema_last: float,
    dema_series: pd.Series,
    close_series: pd.Series,
) -> float:
    """Composite 0–100 score."""
    score = 0.0

    # 35 pts: price above DEMA
    if close_last > dema_last:
        score += 35.0

    # 35 pts: DEMA slope positive
    lookback = 5
    if len(dema_series) > lookback:
        if float(dema_series.iloc[-1]) > float(dema_series.iloc[-1 - lookback]):
            score += 35.0

    # 30 pts: percentile rank of (close − DEMA)/DEMA in 252-bar window
    window = min(252, len(close_series))
    if window >= 10 and len(dema_series) == len(close_series):
        rel = (close_series - dema_series) / dema_series.replace(0.0, float("nan"))
        rel_win = rel.iloc[-window:]
        last_val = float(rel.iloc[-1]) if not pd.isna(rel.iloc[-1]) else 0.0
        pct = float((rel_win < last_val).sum()) / max(1, len(rel_win))
        score += pct * 30.0

    return round(min(100.0, max(0.0, score)), 2)


def _classify_signal(score: float | None) -> DEMASignal:
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
    signal: DEMASignal,
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
    parts.append(f"DEMA({period}) 综合评分 {score:.1f}/100，信号{sig_map.get(signal, signal)}。")
    if price_above is not None:
        parts.append("价格位于 DEMA 上方，趋势偏多。" if price_above else "价格位于 DEMA 下方，趋势偏空。")
    if slope_positive is not None:
        parts.append("DEMA 斜率向上，动能增强。" if slope_positive else "DEMA 斜率向下，动能减弱。")
    parts.append("DEMA 比普通 EMA 滞后更低，对价格变化更为敏感。")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def compute_dema(ticker: str, period: int = 20) -> DEMAData:
    """Fetch OHLCV from yfinance and compute DEMA signal."""
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period="2y")
        if df.empty or len(df) < _MIN_BARS:
            return DEMAData(
                ticker=ticker,
                dema_value=None,
                price_above_dema=None,
                dema_slope_positive=None,
                dema_score=0.0,
                signal="no_data",
                interpretation="数据不足，无法计算 DEMA。",
                as_of_date=str(date.today()),
                data_available=True,
            )

        close = df["Close"].dropna()
        dema_series = _compute_dema_series(close, period)

        dema_last = float(dema_series.iloc[-1])
        close_last = float(close.iloc[-1])
        slope_positive = float(dema_series.iloc[-1]) > float(
            dema_series.iloc[-1 - min(5, len(dema_series) - 1)]
        )
        price_above = close_last > dema_last

        score = _compute_dema_score(
            close_last - dema_last, close_last, dema_last, dema_series, close
        )
        signal = _classify_signal(score)
        interp = _build_interpretation(score, signal, price_above, slope_positive, period)

        as_of = str(df.index[-1].date()) if hasattr(df.index[-1], "date") else str(date.today())

        return DEMAData(
            ticker=ticker,
            dema_value=round(dema_last, 4),
            price_above_dema=price_above,
            dema_slope_positive=slope_positive,
            dema_score=score,
            signal=signal,
            interpretation=interp,
            as_of_date=as_of,
            data_available=True,
        )

    except Exception:
        return DEMAData(
            ticker=ticker,
            dema_value=None,
            price_above_dema=None,
            dema_slope_positive=None,
            dema_score=0.0,
            signal="no_data",
            interpretation="数据获取失败。",
            as_of_date=str(date.today()),
            data_available=False,
        )
