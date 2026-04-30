"""Elder Impulse System — F.80.

Combines two indicators to classify each bar as Green (buy), Red (sell), or Blue (neutral):
  • 13-period EMA slope: rising (+) or falling (−)
  • MACD(12,26,9) histogram: rising (+) or falling (−)

  Green  = EMA rising AND MACD hist rising  → bullish impulse
  Red    = EMA falling AND MACD hist falling → bearish impulse
  Blue   = mixed (neither all-green nor all-red)

Score (0–100):
  35 pts  EMA(13) slope positive (current vs 5-bars-ago)
  35 pts  MACD histogram positive AND rising
  30 pts  percentile rank of (close − EMA13) / EMA13 in rolling 252-bar window
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

ImpulseSignal = Literal["strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"]
ImpulseColor = Literal["green", "red", "blue"]

_MIN_BARS = 35


@dataclass
class ImpulseData:
    ticker: str
    ema13: float | None
    macd_hist: float | None
    impulse_color: ImpulseColor | None   # green / red / blue
    ema_rising: bool | None
    hist_rising: bool | None
    impulse_score: float
    signal: ImpulseSignal
    interpretation: str
    as_of_date: str
    data_available: bool


# ---------------------------------------------------------------------------
# Core math
# ---------------------------------------------------------------------------

def _compute_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _compute_macd_hist(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.Series:
    macd_line = _compute_ema(close, fast) - _compute_ema(close, slow)
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return (macd_line - signal_line).fillna(0.0)


def _classify_impulse_color(ema_rising: bool, hist_rising: bool) -> ImpulseColor:
    if ema_rising and hist_rising:
        return "green"
    if not ema_rising and not hist_rising:
        return "red"
    return "blue"


def _compute_impulse_score(
    close_last: float,
    ema_last: float,
    ema_series: pd.Series,
    hist_series: pd.Series,
    close_series: pd.Series,
) -> float:
    """Composite 0–100 score."""
    score = 0.0

    # 35 pts: EMA13 slope positive
    lookback = 5
    if len(ema_series) > lookback:
        if float(ema_series.iloc[-1]) > float(ema_series.iloc[-1 - lookback]):
            score += 35.0

    # 35 pts: MACD histogram positive AND rising
    hist_last = float(hist_series.iloc[-1])
    if len(hist_series) >= 2:
        hist_prev = float(hist_series.iloc[-2])
        if hist_last > 0.0 and hist_last > hist_prev:
            score += 35.0

    # 30 pts: percentile rank of (close − EMA13) / EMA13
    window = min(252, len(close_series))
    if window >= 10 and len(ema_series) == len(close_series):
        rel = (close_series - ema_series) / ema_series.replace(0.0, float("nan"))
        rel_win = rel.iloc[-window:]
        last_val = float(rel.iloc[-1]) if not pd.isna(rel.iloc[-1]) else 0.0
        pct = float((rel_win < last_val).sum()) / max(1, len(rel_win))
        score += pct * 30.0

    return round(min(100.0, max(0.0, score)), 2)


def _classify_signal(score: float | None) -> ImpulseSignal:
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
    signal: ImpulseSignal,
    impulse_color: ImpulseColor | None,
    ema_rising: bool | None,
    hist_rising: bool | None,
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
    parts.append(f"Elder Impulse 综合评分 {score:.1f}/100，信号{sig_map.get(signal, signal)}。")
    color_map = {"green": "绿柱（买入冲量）", "red": "红柱（卖出冲量）", "blue": "蓝柱（中性信号）"}
    if impulse_color:
        parts.append(f"当前冲量颜色：{color_map.get(impulse_color, impulse_color)}。")
    if ema_rising is not None and hist_rising is not None:
        if ema_rising and hist_rising:
            parts.append("EMA(13) 与 MACD 柱均向上，双重确认多头冲量。")
        elif not ema_rising and not hist_rising:
            parts.append("EMA(13) 与 MACD 柱均向下，双重确认空头冲量。")
        else:
            parts.append("EMA 与 MACD 信号分歧，等待方向确认再行动。")
    parts.append("绿色冲量：趋势向上，系统禁止做空；红色冲量：趋势向下，系统禁止做多。")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def compute_impulse(ticker: str) -> ImpulseData:
    """Fetch OHLCV from yfinance and compute Elder Impulse System."""
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period="2y")
        if df.empty or len(df) < _MIN_BARS:
            return ImpulseData(
                ticker=ticker,
                ema13=None,
                macd_hist=None,
                impulse_color=None,
                ema_rising=None,
                hist_rising=None,
                impulse_score=0.0,
                signal="no_data",
                interpretation="数据不足，无法计算 Elder Impulse。",
                as_of_date=str(date.today()),
                data_available=True,
            )

        close = df["Close"].dropna()
        ema13_series = _compute_ema(close, 13)
        hist_series = _compute_macd_hist(close)

        ema_last = float(ema13_series.iloc[-1])
        close_last = float(close.iloc[-1])
        hist_last = float(hist_series.iloc[-1])

        lookback = 5
        ema_rising = float(ema13_series.iloc[-1]) > float(
            ema13_series.iloc[-1 - min(lookback, len(ema13_series) - 1)]
        )
        hist_rising = (
            len(hist_series) >= 2 and hist_last > float(hist_series.iloc[-2])
        )

        impulse_color = _classify_impulse_color(ema_rising, hist_rising)
        score = _compute_impulse_score(
            close_last, ema_last, ema13_series, hist_series, close
        )
        signal = _classify_signal(score)
        interp = _build_interpretation(score, signal, impulse_color, ema_rising, hist_rising)

        as_of = str(df.index[-1].date()) if hasattr(df.index[-1], "date") else str(date.today())

        return ImpulseData(
            ticker=ticker,
            ema13=round(ema_last, 4),
            macd_hist=round(hist_last, 6),
            impulse_color=impulse_color,
            ema_rising=ema_rising,
            hist_rising=hist_rising,
            impulse_score=score,
            signal=signal,
            interpretation=interp,
            as_of_date=as_of,
            data_available=True,
        )

    except Exception:
        return ImpulseData(
            ticker=ticker,
            ema13=None,
            macd_hist=None,
            impulse_color=None,
            ema_rising=None,
            hist_rising=None,
            impulse_score=0.0,
            signal="no_data",
            interpretation="数据获取失败。",
            as_of_date=str(date.today()),
            data_available=False,
        )
