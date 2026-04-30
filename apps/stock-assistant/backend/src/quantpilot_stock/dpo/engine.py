"""DPO (Detrended Price Oscillator) engine — Phase F.56.

DPO = Close − SMA(n, shifted back by n//2 + 1 bars)

Period n = 20, offset = 11.
Removes the trend to expose short-term cycles.

Score = percentile rank of DPO in last 252 bars × 100.

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

DPOSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_DPO_PERIOD  = 20
_DPO_OFFSET  = _DPO_PERIOD // 2 + 1   # 11
_MIN_BARS    = _DPO_PERIOD + _DPO_OFFSET + 5


@dataclass
class DPOData:
    ticker: str
    dpo_value: float | None = None     # Latest DPO
    dpo_positive: bool = False         # DPO > 0
    dpo_score: float = 50.0           # 0–100 percentile
    signal: DPOSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_dpo_series(
    close: pd.Series,
    period: int = _DPO_PERIOD,
) -> pd.Series:
    """Return DPO series.

    DPO[t] = Close[t] - SMA(period)[t - offset]
    where offset = period // 2 + 1.
    """
    offset = period // 2 + 1
    sma    = close.rolling(period).mean()
    # Shift the SMA forward by *offset* bars so we align the
    # mid-point of the SMA with the current bar.
    dpo = close - sma.shift(offset)
    return dpo.fillna(0.0)


def _compute_dpo_score(
    dpo_val: float,
    dpo_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Percentile rank of dpo_val within last *lookback* bars × 100."""
    window = dpo_series.iloc[-lookback:].dropna()
    if len(window) < 10:
        return float(max(0.0, min(100.0, (dpo_val + 1.0) / 2.0 * 100.0)))
    rank = float((window < dpo_val).mean())
    return round(rank * 100.0, 1)


def _classify_signal(score: float | None) -> DPOSignal:
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
    ticker: str,
    signal: DPOSignal,
    dpo: float,
    score: float,
    positive: bool,
) -> str:
    cycle = "上行周期" if positive else "下行周期"
    labels: dict[DPOSignal, str] = {
        "strong_bull": (
            f"{ticker} DPO {dpo:+.4f}（百分位 {score:.0f}）：{cycle}极强，"
            f"价格大幅高于历史均值。"
        ),
        "bull": (
            f"{ticker} DPO {dpo:+.4f}（百分位 {score:.0f}）：{cycle}偏强，"
            f"去趋势动量偏正。"
        ),
        "neutral": (
            f"{ticker} DPO {dpo:+.4f}（百分位 {score:.0f}）：{cycle}中性，"
            f"价格接近历史均值，无明显周期偏差。"
        ),
        "bear": (
            f"{ticker} DPO {dpo:+.4f}（百分位 {score:.0f}）：{cycle}偏弱，"
            f"去趋势动量偏负。"
        ),
        "strong_bear": (
            f"{ticker} DPO {dpo:+.4f}（百分位 {score:.0f}）：{cycle}极弱，"
            f"价格大幅低于历史均值。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 DPO。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_dpo(ticker: str) -> DPOData:
    """Compute DPO for *ticker*.

    Never raises. Returns DPOData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return DPOData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    if hist.empty or "Close" not in hist.columns:
        return DPOData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 DPO。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()

    if len(close) < _MIN_BARS:
        return DPOData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 DPO。",
            as_of_date=as_of,
        )

    dpo_series = _compute_dpo_series(close)

    dpo_val  = float(dpo_series.iloc[-1])
    positive = dpo_val > 0.0

    score  = _compute_dpo_score(dpo_val, dpo_series)
    signal = _classify_signal(score)
    interp = _build_interpretation(ticker, signal, dpo_val, score, positive)

    return DPOData(
        ticker=ticker,
        dpo_value=round(dpo_val, 4),
        dpo_positive=positive,
        dpo_score=round(score, 1),
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
