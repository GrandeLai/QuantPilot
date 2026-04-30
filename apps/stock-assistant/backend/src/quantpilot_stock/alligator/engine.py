"""Williams Alligator — F.77.

Bill Williams' Alligator indicator uses three Smoothed Moving Averages (SMMA)
of the median price (High+Low)/2, displaced forward:
  Jaw   (Blue):  SMMA(13), shift 8 bars forward
  Teeth (Red):   SMMA(8),  shift 5 bars forward
  Lips  (Green): SMMA(5),  shift 3 bars forward

For analysis we compare current bar values (no shift) to assess trend:
  - Lips > Teeth > Jaw → Alligator eating upward (bullish trend)
  - Lips < Teeth < Jaw → Alligator eating downward (bearish trend)
  - Intertwined       → Alligator sleeping (consolidation)

Score (0–100):
  20 pts  lips > teeth
  20 pts  teeth > jaw
  25 pts  price (close) above jaw
  15 pts  jaw slope positive (rising long-term trend)
  20 pts  percentile of (lips − jaw) / jaw in rolling 252-bar window
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

AlligatorSignal = Literal["strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"]

_MIN_BARS = 50


@dataclass
class AlligatorData:
    ticker: str
    jaw: float | None         # blue line (SMMA 13)
    teeth: float | None       # red line (SMMA 8)
    lips: float | None        # green line (SMMA 5)
    lips_above_teeth: bool | None
    teeth_above_jaw: bool | None
    price_above_jaw: bool | None
    alligator_score: float
    signal: AlligatorSignal
    interpretation: str
    as_of_date: str
    data_available: bool


# ---------------------------------------------------------------------------
# Core math
# ---------------------------------------------------------------------------

def _compute_smma(series: pd.Series, period: int) -> pd.Series:
    """Smoothed Moving Average (SMMA / Wilder's MA) = EMA with alpha=1/period."""
    return series.ewm(alpha=1.0 / period, adjust=False).mean()


def _compute_alligator_series(
    high: pd.Series,
    low: pd.Series,
    jaw_period: int = 13,
    teeth_period: int = 8,
    lips_period: int = 5,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Return (jaw, teeth, lips) SMMA series of median price."""
    median = (high + low) / 2.0
    jaw = _compute_smma(median, jaw_period).ffill().fillna(median)
    teeth = _compute_smma(median, teeth_period).ffill().fillna(median)
    lips = _compute_smma(median, lips_period).ffill().fillna(median)
    return jaw, teeth, lips


def _compute_alligator_score(
    close_last: float,
    jaw_last: float,
    teeth_last: float,
    lips_last: float,
    jaw_series: pd.Series,
    lips_series: pd.Series,
) -> float:
    """Composite 0–100 score."""
    score = 0.0

    # 20 pts: lips above teeth
    if lips_last > teeth_last:
        score += 20.0

    # 20 pts: teeth above jaw
    if teeth_last > jaw_last:
        score += 20.0

    # 25 pts: close above jaw
    if close_last > jaw_last:
        score += 25.0

    # 15 pts: jaw slope positive
    lookback = 5
    if len(jaw_series) > lookback:
        if float(jaw_series.iloc[-1]) > float(jaw_series.iloc[-1 - lookback]):
            score += 15.0

    # 20 pts: percentile of (lips − jaw)/jaw in rolling 252-bar window
    window = min(252, len(lips_series))
    if window >= 10 and len(lips_series) == len(jaw_series):
        spread = (lips_series - jaw_series) / jaw_series.replace(0.0, float("nan"))
        spread_win = spread.iloc[-window:]
        last_val = float(spread.iloc[-1]) if not pd.isna(spread.iloc[-1]) else 0.0
        pct = float((spread_win < last_val).sum()) / max(1, len(spread_win))
        score += pct * 20.0

    return round(min(100.0, max(0.0, score)), 2)


def _classify_signal(score: float | None) -> AlligatorSignal:
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
    signal: AlligatorSignal,
    lips_above_teeth: bool | None,
    teeth_above_jaw: bool | None,
    price_above_jaw: bool | None,
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
    parts.append(f"Williams Alligator 综合评分 {score:.1f}/100，信号{sig_map.get(signal, signal)}。")
    if lips_above_teeth and teeth_above_jaw:
        parts.append("鳄鱼嘴向上展开（唇>齿>颚），趋势强势上行。")
    elif lips_above_teeth is False and teeth_above_jaw is False:
        parts.append("鳄鱼嘴向下展开（唇<齿<颚），趋势强势下行。")
    else:
        parts.append("鳄鱼线交织，市场处于盘整（鳄鱼入睡）状态。")
    if price_above_jaw is not None:
        parts.append("价格位于颚线上方，长期偏多。" if price_above_jaw else "价格位于颚线下方，长期偏空。")
    parts.append("信号启动时机：鳄鱼从睡眠中醒来、三线分叉是进场参考。")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def compute_alligator(ticker: str) -> AlligatorData:
    """Fetch OHLCV from yfinance and compute Williams Alligator signal."""
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period="2y")
        if df.empty or len(df) < _MIN_BARS:
            return AlligatorData(
                ticker=ticker,
                jaw=None,
                teeth=None,
                lips=None,
                lips_above_teeth=None,
                teeth_above_jaw=None,
                price_above_jaw=None,
                alligator_score=0.0,
                signal="no_data",
                interpretation="数据不足，无法计算 Alligator。",
                as_of_date=str(date.today()),
                data_available=True,
            )

        high = df["High"].dropna()
        low = df["Low"].dropna()
        close = df["Close"].dropna()
        jaw_s, teeth_s, lips_s = _compute_alligator_series(high, low)

        jaw_last = float(jaw_s.iloc[-1])
        teeth_last = float(teeth_s.iloc[-1])
        lips_last = float(lips_s.iloc[-1])
        close_last = float(close.iloc[-1])

        lips_above_teeth = lips_last > teeth_last
        teeth_above_jaw = teeth_last > jaw_last
        price_above_jaw = close_last > jaw_last

        score = _compute_alligator_score(
            close_last, jaw_last, teeth_last, lips_last, jaw_s, lips_s
        )
        signal = _classify_signal(score)
        interp = _build_interpretation(
            score, signal, lips_above_teeth, teeth_above_jaw, price_above_jaw
        )

        as_of = str(df.index[-1].date()) if hasattr(df.index[-1], "date") else str(date.today())

        return AlligatorData(
            ticker=ticker,
            jaw=round(jaw_last, 4),
            teeth=round(teeth_last, 4),
            lips=round(lips_last, 4),
            lips_above_teeth=lips_above_teeth,
            teeth_above_jaw=teeth_above_jaw,
            price_above_jaw=price_above_jaw,
            alligator_score=score,
            signal=signal,
            interpretation=interp,
            as_of_date=as_of,
            data_available=True,
        )

    except Exception:
        return AlligatorData(
            ticker=ticker,
            jaw=None,
            teeth=None,
            lips=None,
            lips_above_teeth=None,
            teeth_above_jaw=None,
            price_above_jaw=None,
            alligator_score=0.0,
            signal="no_data",
            interpretation="数据获取失败。",
            as_of_date=str(date.today()),
            data_available=False,
        )
