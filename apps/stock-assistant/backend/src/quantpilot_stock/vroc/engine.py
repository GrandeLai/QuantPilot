"""Volume Rate of Change (VROC) — F.84.

Measures the rate of change in trading volume, indicating the momentum
of volume participation in price moves.

  VROC(n) = (Volume[t] − Volume[t−n]) / Volume[t−n] × 100

  Default: n = 14

Range: unbounded percentage; typical ±100%
  VROC > 0  → volume expanding (confirm trend)
  VROC < 0  → volume contracting (weakening)
  Extreme positive VROC on price breakout → strong confirmation

Score (0–100):
  35 pts  VROC > 0 (volume expanding)
  35 pts  VROC rising (vs previous bar)
  30 pts  percentile rank of VROC in rolling 252-bar window
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

VROCSignal = Literal["strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"]

_MIN_BARS = 20


@dataclass
class VROCData:
    ticker: str
    vroc_value: float | None   # percent
    vroc_score: float
    signal: VROCSignal
    interpretation: str
    as_of_date: str
    data_available: bool


# ---------------------------------------------------------------------------
# Core math
# ---------------------------------------------------------------------------

def _compute_vroc_series(volume: pd.Series, period: int = 14) -> pd.Series:
    """VROC = (vol[t] - vol[t-n]) / vol[t-n] * 100."""
    vol_prev = volume.shift(period)
    vroc = ((volume - vol_prev) / vol_prev.replace(0.0, float("nan"))) * 100.0
    return vroc.fillna(0.0)


def _compute_vroc_score(vroc_series: pd.Series) -> float:
    """Composite 0–100 score."""
    score = 0.0
    vroc_last = float(vroc_series.iloc[-1])

    # 35 pts: VROC > 0
    if vroc_last > 0.0:
        score += 35.0

    # 35 pts: VROC rising vs previous bar
    if len(vroc_series) >= 2:
        if vroc_last > float(vroc_series.iloc[-2]):
            score += 35.0

    # 30 pts: percentile rank of VROC in 252-bar window
    window = min(252, len(vroc_series))
    if window >= 10:
        vroc_win = vroc_series.iloc[-window:]
        pct = float((vroc_win < vroc_last).sum()) / max(1, len(vroc_win))
        score += pct * 30.0

    return round(min(100.0, max(0.0, score)), 2)


def _classify_signal(score: float | None) -> VROCSignal:
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
    signal: VROCSignal,
    vroc: float,
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
    parts.append(f"Volume ROC 综合评分 {score:.1f}/100，信号{sig_map.get(signal, signal)}。")
    parts.append(f"VROC={vroc:.1f}%。")
    if vroc > 50:
        parts.append("成交量大幅扩张（>+50%），当前价格行情获得强力量能支撑。")
    elif vroc > 0:
        parts.append("成交量温和扩张，趋势健康。")
    elif vroc > -30:
        parts.append("成交量小幅萎缩，趋势动能减弱。")
    else:
        parts.append("成交量大幅萎缩（<-30%），趋势可能即将反转或进入横盘。")
    parts.append("VROC 适合配合价格突破信号使用，突破伴随 VROC 暴涨往往可靠性更高。")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def compute_vroc(ticker: str) -> VROCData:
    """Fetch OHLCV from yfinance and compute Volume Rate of Change."""
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period="2y")
        if df.empty or len(df) < _MIN_BARS:
            return VROCData(
                ticker=ticker,
                vroc_value=None,
                vroc_score=0.0,
                signal="no_data",
                interpretation="数据不足，无法计算 Volume ROC。",
                as_of_date=str(date.today()),
                data_available=True,
            )

        volume = df["Volume"].dropna().astype(float)
        vroc_series = _compute_vroc_series(volume)

        vroc_last = float(vroc_series.iloc[-1])
        score = _compute_vroc_score(vroc_series)
        sig = _classify_signal(score)
        interp = _build_interpretation(score, sig, vroc_last)

        as_of = str(df.index[-1].date()) if hasattr(df.index[-1], "date") else str(date.today())

        return VROCData(
            ticker=ticker,
            vroc_value=round(vroc_last, 2),
            vroc_score=score,
            signal=sig,
            interpretation=interp,
            as_of_date=as_of,
            data_available=True,
        )

    except Exception:
        return VROCData(
            ticker=ticker,
            vroc_value=None,
            vroc_score=0.0,
            signal="no_data",
            interpretation="数据获取失败。",
            as_of_date=str(date.today()),
            data_available=False,
        )
