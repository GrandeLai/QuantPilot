"""Parabolic SAR engine — Phase F.48.

Wilder's Parabolic SAR:
  Uptrend:   SAR(t) = SAR(t-1) + AF × (EP - SAR(t-1))
  Downtrend: SAR(t) = SAR(t-1) + AF × (EP - SAR(t-1))

AF starts at 0.02, increments 0.02 each time EP updates, cap at 0.20.
Trend reversal when Close crosses SAR.

Score = percentile rank of (Close/SAR - 1) in the 252-bar window × 100.

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import numpy as np
import pandas as pd
import yfinance as yf

SARSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_AF_INIT = 0.02
_AF_STEP = 0.02
_AF_MAX = 0.20
_MIN_BARS = 30


@dataclass
class SARData:
    ticker: str
    sar: float | None = None             # Latest SAR value
    sar_distance_pct: float | None = None  # (Close - SAR) / Close × 100
    sar_bullish: bool = False            # Close > SAR
    sar_direction: str = ""             # "up" | "down"
    trend_bars: int = 0                  # Consecutive bars in current trend
    sar_score: float = 50.0             # 0-100 percentile-based score
    signal: SARSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_sar_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    af_init: float = _AF_INIT,
    af_step: float = _AF_STEP,
    af_max: float = _AF_MAX,
) -> tuple[pd.Series, pd.Series]:
    """Return (sar_series, bullish_series) aligned with the input index.

    sar_series: SAR value at each bar (NaN for first bar).
    bullish_series: True when Close > SAR.
    """
    n = len(close)
    if n < 2:
        sar_arr = np.full(n, np.nan)
        bull_arr = np.zeros(n, dtype=bool)
        return (
            pd.Series(sar_arr, index=close.index),
            pd.Series(bull_arr, index=close.index),
        )

    high_vals = high.to_numpy(dtype=float)
    low_vals = low.to_numpy(dtype=float)
    close_vals = close.to_numpy(dtype=float)

    sar_arr = np.full(n, np.nan)
    bull_arr = np.zeros(n, dtype=bool)

    # Seed: if bar[1] > bar[0] → start in uptrend
    bullish = close_vals[1] >= close_vals[0]
    if bullish:
        ep = high_vals[0]
        sar_arr[0] = low_vals[0]
    else:
        ep = low_vals[0]
        sar_arr[0] = high_vals[0]

    af = af_init
    bull_arr[0] = bullish

    for i in range(1, n):
        prev_sar = sar_arr[i - 1]
        # Compute new SAR
        new_sar = prev_sar + af * (ep - prev_sar)

        if bullish:
            # SAR must not exceed lowest two prior lows
            min_prev_low = min(low_vals[max(0, i - 2) : i])
            new_sar = min(new_sar, min_prev_low)
            # Check reversal
            if close_vals[i] < new_sar:
                bullish = False
                new_sar = ep  # SAR flips to prior EP
                ep = low_vals[i]
                af = af_init
            else:
                if high_vals[i] > ep:
                    ep = high_vals[i]
                    af = min(af + af_step, af_max)
        else:
            # SAR must not exceed highest two prior highs
            max_prev_high = max(high_vals[max(0, i - 2) : i])
            new_sar = max(new_sar, max_prev_high)
            # Check reversal
            if close_vals[i] > new_sar:
                bullish = True
                new_sar = ep
                ep = high_vals[i]
                af = af_init
            else:
                if low_vals[i] < ep:
                    ep = low_vals[i]
                    af = min(af + af_step, af_max)

        sar_arr[i] = new_sar
        bull_arr[i] = bullish

    return (
        pd.Series(sar_arr, index=close.index),
        pd.Series(bull_arr, index=close.index),
    )


def _compute_distance_series(
    close: pd.Series,
    sar: pd.Series,
) -> pd.Series:
    """(Close - SAR) / Close × 100; NaN where SAR is NaN or Close is 0."""
    safe_close = close.replace(0.0, float("nan"))
    dist = (close - sar) / safe_close * 100.0
    return dist.fillna(0.0)


def _compute_sar_score(
    dist_val: float,
    dist_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Percentile rank of dist_val in the last *lookback* bars × 100."""
    window = dist_series.iloc[-lookback:].dropna()
    if len(window) < 10:
        return float(max(0.0, min(100.0, (dist_val + 10.0) / 20.0 * 100.0)))
    rank = float((window < dist_val).mean())
    return round(rank * 100.0, 1)


def _classify_signal(score: float | None) -> SARSignal:
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


def _count_trend_bars(bullish_series: pd.Series) -> int:
    """Count consecutive bars at end with same bullish/bearish state.

    Positive = uptrend bars, negative = downtrend bars.
    """
    if len(bullish_series) == 0:
        return 0
    is_bull = bool(bullish_series.iloc[-1])
    count = 0
    for b in reversed(bullish_series.to_numpy(dtype=bool)):
        if b == is_bull:
            count += 1
        else:
            break
    return count if is_bull else -count


def _build_interpretation(
    ticker: str,
    signal: SARSignal,
    sar: float,
    dist_pct: float,
    score: float,
    trend_bars: int,
) -> str:
    trend_str = f"已持续 {abs(trend_bars)} 日" if trend_bars != 0 else ""
    labels: dict[SARSignal, str] = {
        "strong_bull": (
            f"{ticker} 价格高于 SAR（{sar:.2f}），偏离 {dist_pct:+.2f}%（百分位 {score:.0f}）"
            f"：趋势强烈向上{('，' + trend_str) if trend_str else ''}。"
        ),
        "bull": (
            f"{ticker} 价格高于 SAR（{sar:.2f}），偏离 {dist_pct:+.2f}%（百分位 {score:.0f}）"
            f"：上升趋势{('，' + trend_str) if trend_str else ''}。"
        ),
        "neutral": (
            f"{ticker} 价格接近 SAR（{sar:.2f}），偏离 {dist_pct:+.2f}%（百分位 {score:.0f}）"
            f"：趋势中性，注意可能的反转。"
        ),
        "bear": (
            f"{ticker} 价格低于 SAR（{sar:.2f}），偏离 {dist_pct:+.2f}%（百分位 {score:.0f}）"
            f"：下降趋势{('，' + trend_str) if trend_str else ''}。"
        ),
        "strong_bear": (
            f"{ticker} 价格远低于 SAR（{sar:.2f}），偏离 {dist_pct:+.2f}%（百分位 {score:.0f}）"
            f"：趋势强烈向下{('，' + trend_str) if trend_str else ''}。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 Parabolic SAR。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_sar(ticker: str) -> SARData:
    """Compute Parabolic SAR data for *ticker*.

    Never raises. Returns SARData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return SARData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    if hist.empty or not {"High", "Low", "Close"}.issubset(hist.columns):
        return SARData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 SAR。",
            as_of_date=as_of,
        )

    high = hist["High"].dropna()
    low = hist["Low"].dropna()
    close = hist["Close"].dropna()
    # Align all three
    idx = high.index.intersection(low.index).intersection(close.index)
    high, low, close = high.loc[idx], low.loc[idx], close.loc[idx]

    if len(close) < _MIN_BARS:
        return SARData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 SAR。",
            as_of_date=as_of,
        )

    sar_series, bull_series = _compute_sar_series(high, low, close)
    dist_series = _compute_distance_series(close, sar_series)

    sar_val = float(sar_series.iloc[-1])
    dist_val = float(dist_series.iloc[-1])
    sar_bullish = bool(bull_series.iloc[-1])
    sar_direction = "up" if sar_bullish else "down"
    trend_bars = _count_trend_bars(bull_series)

    sar_score = _compute_sar_score(dist_val, dist_series)
    signal = _classify_signal(sar_score)
    interpretation = _build_interpretation(
        ticker, signal, sar_val, dist_val, sar_score, trend_bars
    )

    return SARData(
        ticker=ticker,
        sar=round(sar_val, 4),
        sar_distance_pct=round(dist_val, 3),
        sar_bullish=sar_bullish,
        sar_direction=sar_direction,
        trend_bars=trend_bars,
        sar_score=round(sar_score, 1),
        signal=signal,
        interpretation=interpretation,
        as_of_date=as_of,
        data_available=True,
    )
