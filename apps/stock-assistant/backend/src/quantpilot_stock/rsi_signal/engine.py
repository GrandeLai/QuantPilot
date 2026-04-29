"""RSI Divergence Signal engine — Phase F.39.

Computes RSI(14) with Wilder smoothing, overbought/oversold zones,
simple bullish/bearish divergence detection, and composite momentum
score (0-100).

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import yfinance as yf

RSISignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]


@dataclass
class RSIData:
    ticker: str
    rsi: float | None = None             # RSI value 0-100
    prev_rsi: float | None = None        # Previous bar RSI
    rsi_direction: str = ""              # "rising" | "falling" | "flat"
    overbought: bool = False             # rsi > 70
    oversold: bool = False               # rsi < 30
    bullish_divergence: bool = False     # price lower low, RSI higher low
    bearish_divergence: bool = False     # price higher high, RSI lower high
    rsi_score: float = 50.0              # 0-100 composite score
    signal: RSISignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_MIN_BARS = 30   # 14 (RSI period) + 14 (divergence lookback) + 2 guard
_DIV_LOOKBACK = 20


def _compute_rsi_series(
    close: "pd.Series",  # type: ignore[name-defined]  # noqa: F821
    period: int = 14,
) -> "pd.Series":  # type: ignore[name-defined]  # noqa: F821
    """Compute RSI using Wilder smoothing (EWM with alpha = 1/period)."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)

    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    # Avoid division by zero: when avg_loss == 0, RSI = 100
    rs = avg_gain / avg_loss.replace(0, float("nan"))
    rsi = 100.0 - 100.0 / (1.0 + rs)
    rsi = rsi.fillna(100.0)
    return rsi


def _detect_divergence(
    close: "pd.Series",  # type: ignore[name-defined]  # noqa: F821
    rsi_series: "pd.Series",  # type: ignore[name-defined]  # noqa: F821
    lookback: int = _DIV_LOOKBACK,
) -> tuple[bool, bool]:
    """Detect simple bullish and bearish divergence.

    Bullish: price making lower lows while RSI making higher lows.
    Bearish: price making higher highs while RSI making lower highs.

    Returns (bullish_divergence, bearish_divergence).
    """
    if len(close) < lookback + 2:
        return False, False

    prices = list(close.iloc[-lookback:])
    rsis = list(rsi_series.iloc[-lookback:])
    n = len(prices)

    # Collect troughs (local minima)
    troughs: list[tuple[int, float, float]] = []
    for i in range(1, n - 1):
        if prices[i] <= prices[i - 1] and prices[i] <= prices[i + 1]:
            troughs.append((i, prices[i], rsis[i]))

    # Collect peaks (local maxima)
    peaks: list[tuple[int, float, float]] = []
    for i in range(1, n - 1):
        if prices[i] >= prices[i - 1] and prices[i] >= prices[i + 1]:
            peaks.append((i, prices[i], rsis[i]))

    bullish_div = False
    bearish_div = False

    # Bullish divergence: two troughs where price lower but RSI higher
    if len(troughs) >= 2:
        _, p1, r1 = troughs[-2]
        _, p2, r2 = troughs[-1]
        if p2 < p1 and r2 > r1:
            bullish_div = True

    # Bearish divergence: two peaks where price higher but RSI lower
    if len(peaks) >= 2:
        _, p1, r1 = peaks[-2]
        _, p2, r2 = peaks[-1]
        if p2 > p1 and r2 < r1:
            bearish_div = True

    return bullish_div, bearish_div


def _compute_rsi_score(
    rsi: float | None,
    bullish_divergence: bool,
    bearish_divergence: bool,
) -> float:
    """Composite RSI score in [0, 100].

    Base: RSI value (0-100), already in range.
    Divergence adjustment: ±8 points.
    """
    if rsi is None:
        return 50.0

    score = rsi
    if bullish_divergence:
        score += 8.0
    if bearish_divergence:
        score -= 8.0
    return float(max(0.0, min(100.0, score)))


def _classify_signal(rsi_score: float | None) -> RSISignal:
    if rsi_score is None:
        return "no_data"
    if rsi_score >= 80:
        return "strong_bull"
    if rsi_score >= 60:
        return "bull"
    if rsi_score >= 40:
        return "neutral"
    if rsi_score >= 20:
        return "bear"
    return "strong_bear"


def _build_interpretation(
    ticker: str,
    signal: RSISignal,
    rsi: float | None,
    rsi_score: float,
    overbought: bool,
    oversold: bool,
    bullish_divergence: bool,
    bearish_divergence: bool,
) -> str:
    labels: dict[RSISignal, str] = {
        "strong_bull": (
            f"{ticker} RSI={rsi:.1f} 评分 {rsi_score:.0f}：强势多头动能，RSI 在高位运行。"
            if rsi is not None else f"{ticker} 强势多头动能。"
        ),
        "bull": (
            f"{ticker} RSI={rsi:.1f} 评分 {rsi_score:.0f}：多头动能，价格趋势向上。"
            if rsi is not None else f"{ticker} 多头动能。"
        ),
        "neutral": (
            f"{ticker} RSI={rsi:.1f} 评分 {rsi_score:.0f}：中性，RSI 在 40-60 范围内，无明显方向。"
            if rsi is not None else f"{ticker} 中性。"
        ),
        "bear": (
            f"{ticker} RSI={rsi:.1f} 评分 {rsi_score:.0f}：空头动能，价格趋势向下。"
            if rsi is not None else f"{ticker} 空头动能。"
        ),
        "strong_bear": (
            f"{ticker} RSI={rsi:.1f} 评分 {rsi_score:.0f}：强势空头动能，RSI 在低位运行。"
            if rsi is not None else f"{ticker} 强势空头动能。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 RSI。",
    }
    parts = [labels.get(signal, "")]
    if overbought:
        parts.append("（RSI > 70 超买区间）")
    elif oversold:
        parts.append("（RSI < 30 超卖区间）")
    if bullish_divergence:
        parts.append("（检测到看涨背离：价格创新低而 RSI 未创新低）")
    elif bearish_divergence:
        parts.append("（检测到看跌背离：价格创新高而 RSI 未创新高）")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_rsi_signal(ticker: str) -> RSIData:
    """Compute RSI signal data for *ticker*.

    Never raises. Returns RSIData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1y", interval="1d")
    except Exception:
        return RSIData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    if hist.empty or "Close" not in hist.columns:
        return RSIData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 RSI。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()

    if len(close) < _MIN_BARS:
        return RSIData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 RSI。",
            as_of_date=as_of,
        )

    rsi_series = _compute_rsi_series(close)
    rsi_val = float(rsi_series.iloc[-1])
    prev_rsi_val = float(rsi_series.iloc[-2]) if len(rsi_series) >= 2 else None

    rsi_direction = "flat"
    if prev_rsi_val is not None:
        diff = rsi_val - prev_rsi_val
        if diff > 0.5:
            rsi_direction = "rising"
        elif diff < -0.5:
            rsi_direction = "falling"

    overbought = rsi_val > 70.0
    oversold = rsi_val < 30.0

    bullish_div, bearish_div = _detect_divergence(close, rsi_series)

    rsi_score = _compute_rsi_score(rsi_val, bullish_div, bearish_div)
    signal = _classify_signal(rsi_score)

    interpretation = _build_interpretation(
        ticker, signal, rsi_val, rsi_score,
        overbought, oversold, bullish_div, bearish_div,
    )

    return RSIData(
        ticker=ticker,
        rsi=round(rsi_val, 2),
        prev_rsi=round(prev_rsi_val, 2) if prev_rsi_val is not None else None,
        rsi_direction=rsi_direction,
        overbought=overbought,
        oversold=oversold,
        bullish_divergence=bullish_div,
        bearish_divergence=bearish_div,
        rsi_score=round(rsi_score, 1),
        signal=signal,
        interpretation=interpretation,
        as_of_date=as_of,
        data_available=True,
    )
