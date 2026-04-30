"""Keltner Channel engine — Phase F.50.

Middle : EMA(close, 20)
Upper  : EMA + 2 × ATR(10)   [ATR via Wilder EWM: alpha=1/10]
Lower  : EMA − 2 × ATR(10)

Position within channel (0-100):
  kc_position = (Close − Lower) / (Upper − Lower) × 100   clipped [0, 100]
  (0 = at or below lower band; 100 = at or above upper band)

Score = percentile rank of kc_position in last 252 bars × 100.

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

KeltnerSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_EMA_PERIOD = 20
_ATR_PERIOD = 10
_ATR_MULT   = 2.0
_MIN_BARS   = 30


@dataclass
class KeltnerData:
    ticker: str
    upper: float | None = None             # Upper band
    middle: float | None = None            # EMA (middle)
    lower: float | None = None             # Lower band
    kc_position: float | None = None       # 0-100 within channel
    above_upper: bool = False              # Close > upper band
    below_lower: bool = False              # Close < lower band
    channel_width_pct: float | None = None # (Upper-Lower)/EMA × 100
    kc_score: float = 50.0                # 0-100 percentile-based score
    signal: KeltnerSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_atr_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = _ATR_PERIOD,
) -> pd.Series:
    """Wilder ATR (EWM alpha=1/period)."""
    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low,
         (high - prev_close).abs(),
         (low  - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()


def _compute_keltner_bands(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    ema_period: int = _EMA_PERIOD,
    atr_period: int = _ATR_PERIOD,
    multiplier: float = _ATR_MULT,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Return (upper, middle, lower) Keltner Channel series."""
    middle = close.ewm(span=ema_period, adjust=False).mean()
    atr    = _compute_atr_series(high, low, close, atr_period)
    upper  = middle + multiplier * atr
    lower  = middle - multiplier * atr
    return upper, middle, lower


def _compute_position(
    close: pd.Series,
    upper: pd.Series,
    lower: pd.Series,
) -> pd.Series:
    """(Close − Lower) / (Upper − Lower) × 100, clipped [0, 100]."""
    band_width = (upper - lower).replace(0.0, float("nan"))
    pos = (close - lower) / band_width * 100.0
    pos = pos.clip(0.0, 100.0)
    return pos.fillna(50.0)


def _compute_kc_score(
    pos_val: float,
    pos_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Percentile rank of pos_val within last *lookback* bars × 100."""
    window = pos_series.iloc[-lookback:].dropna()
    if len(window) < 10:
        return float(max(0.0, min(100.0, pos_val)))
    rank = float((window < pos_val).mean())
    return round(rank * 100.0, 1)


def _classify_signal(score: float | None) -> KeltnerSignal:
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
    signal: KeltnerSignal,
    upper: float,
    middle: float,
    lower: float,
    pos: float,
    score: float,
    above_upper: bool,
    below_lower: bool,
) -> str:
    extra = ""
    if above_upper:
        extra = "（突破上轨，可能超买或趋势延续）"
    elif below_lower:
        extra = "（跌破下轨，可能超卖或趋势加速）"

    labels: dict[KeltnerSignal, str] = {
        "strong_bull": (
            f"{ticker} 价格处于 Keltner 上方区域（位置 {pos:.0f}/100，百分位 {score:.0f}）"
            f"：强势多头{extra}。上轨 {upper:.2f} / 中轨 {middle:.2f} / 下轨 {lower:.2f}。"
        ),
        "bull": (
            f"{ticker} 价格处于 Keltner 中上区间（位置 {pos:.0f}/100，百分位 {score:.0f}）"
            f"：偏多头{extra}。上轨 {upper:.2f} / 中轨 {middle:.2f} / 下轨 {lower:.2f}。"
        ),
        "neutral": (
            f"{ticker} 价格处于 Keltner 中间区间（位置 {pos:.0f}/100，百分位 {score:.0f}）"
            f"：多空均衡{extra}。上轨 {upper:.2f} / 中轨 {middle:.2f} / 下轨 {lower:.2f}。"
        ),
        "bear": (
            f"{ticker} 价格处于 Keltner 中下区间（位置 {pos:.0f}/100，百分位 {score:.0f}）"
            f"：偏空头{extra}。上轨 {upper:.2f} / 中轨 {middle:.2f} / 下轨 {lower:.2f}。"
        ),
        "strong_bear": (
            f"{ticker} 价格处于 Keltner 下方区域（位置 {pos:.0f}/100，百分位 {score:.0f}）"
            f"：强势空头{extra}。上轨 {upper:.2f} / 中轨 {middle:.2f} / 下轨 {lower:.2f}。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 Keltner Channel。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_keltner(ticker: str) -> KeltnerData:
    """Compute Keltner Channel data for *ticker*.

    Never raises. Returns KeltnerData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return KeltnerData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    required = {"High", "Low", "Close"}
    if hist.empty or not required.issubset(hist.columns):
        return KeltnerData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 Keltner Channel。",
            as_of_date=as_of,
        )

    idx   = (hist["High"].dropna().index
             .intersection(hist["Low"].dropna().index)
             .intersection(hist["Close"].dropna().index))
    high  = hist["High"].loc[idx]
    low   = hist["Low"].loc[idx]
    close = hist["Close"].loc[idx]

    if len(close) < _MIN_BARS:
        return KeltnerData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 Keltner Channel。",
            as_of_date=as_of,
        )

    upper_s, middle_s, lower_s = _compute_keltner_bands(high, low, close)
    pos_s = _compute_position(close, upper_s, lower_s)

    upper_val  = float(upper_s.iloc[-1])
    middle_val = float(middle_s.iloc[-1])
    lower_val  = float(lower_s.iloc[-1])
    close_val  = float(close.iloc[-1])
    pos_val    = float(pos_s.iloc[-1])

    above_upper = close_val > upper_val
    below_lower = close_val < lower_val
    width_pct   = ((upper_val - lower_val) / middle_val * 100.0
                   if middle_val != 0 else None)

    score       = _compute_kc_score(pos_val, pos_s)
    signal      = _classify_signal(score)
    interp      = _build_interpretation(
        ticker, signal, upper_val, middle_val, lower_val,
        pos_val, score, above_upper, below_lower,
    )

    return KeltnerData(
        ticker=ticker,
        upper=round(upper_val, 4),
        middle=round(middle_val, 4),
        lower=round(lower_val, 4),
        kc_position=round(pos_val, 1),
        above_upper=above_upper,
        below_lower=below_lower,
        channel_width_pct=round(width_pct, 2) if width_pct is not None else None,
        kc_score=round(score, 1),
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
