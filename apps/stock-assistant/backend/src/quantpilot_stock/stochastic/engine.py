"""Stochastic Oscillator engine — Phase F.40.

Computes Full Stochastic (%K14, %D3), overbought/oversold zones,
%K/%D crossover detection, and composite momentum score (0-100).

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import yfinance as yf

StochasticSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]


@dataclass
class StochasticData:
    ticker: str
    k: float | None = None              # %K (0-100)
    d: float | None = None              # %D = SMA3(%K) (0-100)
    prev_k: float | None = None
    prev_d: float | None = None
    overbought: bool = False            # k > 80
    oversold: bool = False              # k < 20
    k_above_d: bool = False             # %K > %D (bullish)
    recent_bull_cross: bool = False     # %K recently crossed above %D
    recent_bear_cross: bool = False     # %K recently crossed below %D
    stoch_score: float = 50.0           # 0-100
    signal: StochasticSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_MIN_BARS = 20   # 14 (%K period) + 3 (%D period) + 3 guard


def _compute_stochastic_series(
    high: "pd.Series",   # type: ignore[name-defined]  # noqa: F821
    low: "pd.Series",    # type: ignore[name-defined]  # noqa: F821
    close: "pd.Series",  # type: ignore[name-defined]  # noqa: F821
    k_period: int = 14,
    d_period: int = 3,
) -> tuple["pd.Series", "pd.Series"]:  # type: ignore[name-defined]  # noqa: F821
    """Return (%K_series, %D_series)."""
    lowest_low = low.rolling(k_period).min()
    highest_high = high.rolling(k_period).max()

    range_hh_ll = (highest_high - lowest_low).replace(0, float("nan"))
    k_series = (close - lowest_low) / range_hh_ll * 100.0
    k_series = k_series.fillna(50.0)  # flat range → 50

    d_series = k_series.rolling(d_period).mean()
    return k_series, d_series


def _detect_crossover(
    k_series: "pd.Series",  # type: ignore[name-defined]  # noqa: F821
    d_series: "pd.Series",  # type: ignore[name-defined]  # noqa: F821
    lookback: int = 3,
) -> tuple[bool, bool]:
    """Detect %K/%D crossover in last *lookback* bars.

    Returns (recent_bull_cross, recent_bear_cross).
    """
    n = len(k_series)
    if n < lookback + 2:
        return False, False

    bull_cross = False
    bear_cross = False
    for i in range(-lookback, 0):
        prev_k = float(k_series.iloc[i - 1])
        curr_k = float(k_series.iloc[i])
        prev_d = float(d_series.iloc[i - 1])
        curr_d = float(d_series.iloc[i])
        import math
        if math.isnan(prev_k) or math.isnan(curr_k) or math.isnan(prev_d) or math.isnan(curr_d):
            continue
        if prev_k <= prev_d and curr_k > curr_d:
            bull_cross = True
        elif prev_k >= prev_d and curr_k < curr_d:
            bear_cross = True

    return bull_cross, bear_cross


def _compute_stoch_score(
    k: float | None,
    d: float | None,
    recent_bull_cross: bool,
    recent_bear_cross: bool,
) -> float:
    """Composite stochastic score in [0, 100].

    Base: %K value (0-100, already in target range).
    Adjustments:
      %K > %D (bull): +5
      %K < %D (bear): -5
      Recent bull cross: +5
      Recent bear cross: -5
    """
    if k is None:
        return 50.0

    score = k

    if d is not None:
        if k > d:
            score += 5.0
        elif k < d:
            score -= 5.0

    if recent_bull_cross:
        score += 5.0
    if recent_bear_cross:
        score -= 5.0

    return float(max(0.0, min(100.0, score)))


def _classify_signal(stoch_score: float | None) -> StochasticSignal:
    if stoch_score is None:
        return "no_data"
    if stoch_score >= 80:
        return "strong_bull"
    if stoch_score >= 60:
        return "bull"
    if stoch_score >= 40:
        return "neutral"
    if stoch_score >= 20:
        return "bear"
    return "strong_bear"


def _build_interpretation(
    ticker: str,
    signal: StochasticSignal,
    k: float | None,
    d: float | None,
    stoch_score: float,
    overbought: bool,
    oversold: bool,
    recent_bull_cross: bool,
    recent_bear_cross: bool,
) -> str:
    labels: dict[StochasticSignal, str] = {
        "strong_bull": (
            f"{ticker} 随机评分 {stoch_score:.0f}：%K={k:.1f}，强势多头动能。"
            if k is not None else f"{ticker} 强势多头动能。"
        ),
        "bull": (
            f"{ticker} 随机评分 {stoch_score:.0f}：%K={k:.1f}，多头动能，趋势向上。"
            if k is not None else f"{ticker} 多头动能。"
        ),
        "neutral": (
            f"{ticker} 随机评分 {stoch_score:.0f}：%K={k:.1f}，中性，等待方向确认。"
            if k is not None else f"{ticker} 中性。"
        ),
        "bear": (
            f"{ticker} 随机评分 {stoch_score:.0f}：%K={k:.1f}，空头动能，趋势向下。"
            if k is not None else f"{ticker} 空头动能。"
        ),
        "strong_bear": (
            f"{ticker} 随机评分 {stoch_score:.0f}：%K={k:.1f}，强势空头动能。"
            if k is not None else f"{ticker} 强势空头动能。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算随机指标。",
    }
    parts = [labels.get(signal, "")]
    if recent_bull_cross:
        parts.append("（近期 %K 上穿 %D 金叉）")
    elif recent_bear_cross:
        parts.append("（近期 %K 下穿 %D 死叉）")
    elif d is not None and k is not None:
        if k > d:
            parts.append(f"（%K={k:.1f} 在 %D={d:.1f} 上方，看涨）")
        else:
            parts.append(f"（%K={k:.1f} 在 %D={d:.1f} 下方，看跌）")
    if overbought:
        parts.append("（超买区间 %K > 80）")
    elif oversold:
        parts.append("（超卖区间 %K < 20）")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_stochastic(ticker: str) -> StochasticData:
    """Compute Stochastic Oscillator data for *ticker*.

    Never raises. Returns StochasticData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1y", interval="1d")
    except Exception:
        return StochasticData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    if hist.empty or not {"High", "Low", "Close"}.issubset(hist.columns):
        return StochasticData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算随机指标。",
            as_of_date=as_of,
        )

    high = hist["High"].dropna()
    low = hist["Low"].dropna()
    close = hist["Close"].dropna()
    min_len = min(len(high), len(low), len(close))

    if min_len < _MIN_BARS:
        return StochasticData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算随机指标。",
            as_of_date=as_of,
        )

    # Align by index
    common_idx = close.index.intersection(high.index).intersection(low.index)
    high = high.loc[common_idx]
    low = low.loc[common_idx]
    close = close.loc[common_idx]

    k_series, d_series = _compute_stochastic_series(high, low, close)

    k_val = float(k_series.iloc[-1])
    d_val_raw = d_series.iloc[-1]
    d_val: float | None = float(d_val_raw) if not __import__("math").isnan(float(d_val_raw)) else None

    prev_k = float(k_series.iloc[-2]) if len(k_series) >= 2 else None
    prev_d_raw = d_series.iloc[-2] if len(d_series) >= 2 else None
    prev_d: float | None = float(prev_d_raw) if prev_d_raw is not None and not __import__("math").isnan(float(prev_d_raw)) else None

    overbought = k_val > 80.0
    oversold = k_val < 20.0
    k_above_d = d_val is not None and k_val > d_val

    recent_bull_cross, recent_bear_cross = _detect_crossover(k_series, d_series)

    stoch_score = _compute_stoch_score(k_val, d_val, recent_bull_cross, recent_bear_cross)
    signal = _classify_signal(stoch_score)

    interpretation = _build_interpretation(
        ticker, signal, k_val, d_val, stoch_score,
        overbought, oversold, recent_bull_cross, recent_bear_cross,
    )

    return StochasticData(
        ticker=ticker,
        k=round(k_val, 2),
        d=round(d_val, 2) if d_val is not None else None,
        prev_k=round(prev_k, 2) if prev_k is not None else None,
        prev_d=round(prev_d, 2) if prev_d is not None else None,
        overbought=overbought,
        oversold=oversold,
        k_above_d=k_above_d,
        recent_bull_cross=recent_bull_cross,
        recent_bear_cross=recent_bear_cross,
        stoch_score=round(stoch_score, 1),
        signal=signal,
        interpretation=interpretation,
        as_of_date=as_of,
        data_available=True,
    )
