"""ADX Trend Strength Indicator engine — Phase F.35.

Implements Wilder's Average Directional Index (ADX) with +DI/-DI directional
movement indicators. ADX measures pure trend strength (0-100); +DI vs -DI
determines direction.

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

TrendSignal = Literal[
    "strong_uptrend",
    "uptrend",
    "ranging",
    "downtrend",
    "strong_downtrend",
    "no_data",
]

TrendStrength = Literal["strong", "moderate", "weak", "none"]

_PERIOD = 14  # Wilder's standard period


@dataclass
class ADXData:
    ticker: str
    adx: float | None = None
    plus_di: float | None = None
    minus_di: float | None = None
    atr: float | None = None
    signal: TrendSignal = "no_data"
    trend_strength: TrendStrength = "none"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _wilder_smooth(series: pd.Series, period: int) -> pd.Series:
    """Apply Wilder's smoothing (EWM with alpha=1/period)."""
    return series.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()


def _compute_adx(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = _PERIOD,
) -> tuple[float | None, float | None, float | None, float | None]:
    """Compute (ADX, +DI, -DI, ATR) from OHLC data.

    Returns (None, None, None, None) if insufficient data.
    """
    min_bars = period * 3  # need enough bars for Wilder smoothing to stabilize
    if len(close) < min_bars:
        return None, None, None, None

    prev_close = close.shift(1)
    prev_high = high.shift(1)
    prev_low = low.shift(1)

    # True Range
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)

    # Directional Movement
    up_move = high - prev_high
    down_move = prev_low - low

    plus_dm = pd.Series(0.0, index=close.index)
    minus_dm = pd.Series(0.0, index=close.index)

    plus_dm[up_move > down_move] = up_move[up_move > down_move].clip(lower=0)
    minus_dm[down_move > up_move] = down_move[down_move > up_move].clip(lower=0)

    # Wilder smoothing
    atr_s = _wilder_smooth(tr, period)
    plus_dm_s = _wilder_smooth(plus_dm, period)
    minus_dm_s = _wilder_smooth(minus_dm, period)

    # Avoid division by zero
    atr_last = float(atr_s.iloc[-1])
    if atr_last <= 0:
        return None, None, None, None

    plus_di = 100.0 * float(plus_dm_s.iloc[-1]) / atr_last
    minus_di = 100.0 * float(minus_dm_s.iloc[-1]) / atr_last

    di_sum = plus_di + minus_di
    if di_sum <= 0:
        return None, None, None, atr_last

    dx_series = 100.0 * (plus_dm_s - minus_dm_s).abs() / (plus_dm_s + minus_dm_s).replace(0, float("nan"))
    adx = float(_wilder_smooth(dx_series.dropna(), period).iloc[-1])

    return adx, plus_di, minus_di, atr_last


def _classify_signal(
    adx: float | None,
    plus_di: float | None,
    minus_di: float | None,
) -> TrendSignal:
    """Classify trend signal based on ADX and DI values."""
    if adx is None or plus_di is None or minus_di is None:
        return "no_data"
    if adx < 20:
        return "ranging"
    if plus_di > minus_di:
        return "strong_uptrend" if adx >= 40 else "uptrend"
    return "strong_downtrend" if adx >= 40 else "downtrend"


def _classify_strength(adx: float | None) -> TrendStrength:
    if adx is None:
        return "none"
    if adx >= 40:
        return "strong"
    if adx >= 25:
        return "moderate"
    if adx >= 15:
        return "weak"
    return "none"


def _build_interpretation(
    ticker: str,
    signal: TrendSignal,
    adx: float | None,
    plus_di: float | None,
    minus_di: float | None,
    strength: TrendStrength,
) -> str:
    strength_labels = {
        "strong": "极强趋势",
        "moderate": "中等趋势",
        "weak": "弱趋势",
        "none": "无趋势/盘整",
    }
    signal_labels: dict[TrendSignal, str] = {
        "strong_uptrend": f"{ticker} ADX={adx:.1f}：强上升趋势，+DI({plus_di:.1f}) >> -DI({minus_di:.1f})，趋势追踪策略有效。",
        "uptrend": f"{ticker} ADX={adx:.1f}：上升趋势，+DI({plus_di:.1f}) > -DI({minus_di:.1f})，适合趋势跟随入场。",
        "ranging": f"{ticker} ADX={adx:.1f}：趋势较弱（盘整），适合均值回归策略，不宜趋势追踪。",
        "downtrend": f"{ticker} ADX={adx:.1f}：下降趋势，-DI({minus_di:.1f}) > +DI({plus_di:.1f})，注意风险或考虑做空。",
        "strong_downtrend": f"{ticker} ADX={adx:.1f}：强下降趋势，-DI({minus_di:.1f}) >> +DI({plus_di:.1f})，不宜多头入场。",
        "no_data": f"{ticker} 数据不足，无法计算 ADX 趋势指标。",
    }
    if adx is None:
        return signal_labels.get("no_data", "")
    base = signal_labels.get(signal, "")
    return f"{base} 趋势强度：{strength_labels.get(strength, '未知')}。"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_adx_trend(ticker: str, period: int = _PERIOD) -> ADXData:
    """Compute ADX trend strength data for *ticker*.

    Never raises. Returns ADXData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1y", interval="1d")
    except Exception:
        return ADXData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    required_cols = {"High", "Low", "Close"}
    if hist.empty or not required_cols.issubset(hist.columns):
        return ADXData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 ADX。",
            as_of_date=as_of,
        )

    high = hist["High"].dropna()
    low = hist["Low"].dropna()
    close = hist["Close"].dropna()

    if len(close) < 30:
        return ADXData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 30 个交易日，无法计算 ADX。",
            as_of_date=as_of,
        )

    adx, plus_di, minus_di, atr = _compute_adx(high, low, close, period)

    if adx is None:
        return ADXData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} ADX 计算失败，可能因数据量不足。",
            as_of_date=as_of,
        )

    signal = _classify_signal(adx, plus_di, minus_di)
    strength = _classify_strength(adx)
    interpretation = _build_interpretation(ticker, signal, adx, plus_di, minus_di, strength)

    return ADXData(
        ticker=ticker,
        adx=round(adx, 2),
        plus_di=round(plus_di, 2) if plus_di is not None else None,
        minus_di=round(minus_di, 2) if minus_di is not None else None,
        atr=round(atr, 4) if atr is not None else None,
        signal=signal,
        trend_strength=strength,
        interpretation=interpretation,
        as_of_date=as_of,
        data_available=True,
    )
