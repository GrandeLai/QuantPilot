"""Moving Average Alignment Score engine — Phase F.36.

Computes multi-timeframe moving average alignment (SMA20/50/200),
golden/death cross state, and a composite bull/bear alignment score (0-100).

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import yfinance as yf

MASignal = Literal[
    "full_bull",
    "partial_bull",
    "neutral",
    "partial_bear",
    "full_bear",
    "no_data",
]


@dataclass
class MAAlignmentData:
    ticker: str
    price: float | None = None
    sma20: float | None = None
    sma50: float | None = None
    sma200: float | None = None
    dist_from_20: float | None = None   # (price - sma20) / sma20
    dist_from_50: float | None = None
    dist_from_200: float | None = None
    ma_score: float = 50.0              # 0-100
    golden_cross: bool = False          # SMA50 > SMA200
    full_bull_align: bool = False       # SMA20 > SMA50 > SMA200 and price > SMA20
    full_bear_align: bool = False       # SMA200 > SMA50 > SMA20 and price < SMA200
    signal: MASignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_ma_score(
    price: float,
    sma20: float | None,
    sma50: float | None,
    sma200: float | None,
) -> float:
    """Compute composite MA alignment score in [0, 100].

    Base score per condition (max raw = 7, min raw = -2):
      +1 each: price>SMA20, price>SMA50, price>SMA200
      +1 each: SMA20>SMA50, SMA50>SMA200
      +2 bonus: full bull alignment (all 5 above true)
      -2 penalty: full bear alignment (SMA200>SMA50>SMA20 and price<SMA200)

    Linear map: raw [-2, 7] → [0, 100].
    """
    raw = 0.0

    # Price vs MAs
    if sma20 is not None and price > sma20:
        raw += 1.0
    if sma50 is not None and price > sma50:
        raw += 1.0
    if sma200 is not None and price > sma200:
        raw += 1.0

    # MA stacking
    if sma20 is not None and sma50 is not None and sma20 > sma50:
        raw += 1.0
    if sma50 is not None and sma200 is not None and sma50 > sma200:
        raw += 1.0

    # Alignment bonus/penalty
    full_bull = (
        sma20 is not None and sma50 is not None and sma200 is not None
        and price > sma20 > sma50 > sma200
    )
    full_bear = (
        sma200 is not None and sma50 is not None and sma20 is not None
        and price < sma200 > sma50 > sma20  # type: ignore[operator]
    )
    # Correct full bear: SMA200 > SMA50 > SMA20 and price < SMA20
    full_bear = (
        sma200 is not None and sma50 is not None and sma20 is not None
        and sma200 > sma50 > sma20  # type: ignore[operator]
        and price < sma20
    )

    if full_bull:
        raw += 2.0
    if full_bear:
        raw -= 2.0

    # Map [-2, 7] → [0, 100]
    raw_min, raw_max = -2.0, 7.0
    normalized = (raw - raw_min) / (raw_max - raw_min) * 100.0
    return float(max(0.0, min(100.0, normalized)))


def _classify_signal(ma_score: float | None) -> MASignal:
    """Classify signal based on composite MA score."""
    if ma_score is None:
        return "no_data"
    if ma_score >= 80:
        return "full_bull"
    if ma_score >= 60:
        return "partial_bull"
    if ma_score >= 40:
        return "neutral"
    if ma_score >= 20:
        return "partial_bear"
    return "full_bear"


def _build_interpretation(
    ticker: str,
    signal: MASignal,
    ma_score: float,
    price: float | None,
    sma20: float | None,
    sma50: float | None,
    sma200: float | None,
    golden_cross: bool,
    full_bull: bool,
    full_bear: bool,
) -> str:
    labels: dict[MASignal, str] = {
        "full_bull": f"{ticker} MA评分 {ma_score:.0f}：完美多头排列，三线上升且价格在均线上方，趋势极强。",
        "partial_bull": f"{ticker} MA评分 {ma_score:.0f}：部分多头排列，整体偏多头，但均线结构尚未完全理顺。",
        "neutral": f"{ticker} MA评分 {ma_score:.0f}：均线中性，多空力量均衡，等待方向确认。",
        "partial_bear": f"{ticker} MA评分 {ma_score:.0f}：部分空头排列，整体偏空，但跌势尚未完全确立。",
        "full_bear": f"{ticker} MA评分 {ma_score:.0f}：完美空头排列，三线下行且价格在均线下方，下跌趋势明确。",
        "no_data": f"{ticker} 数据不足，无法计算均线排列评分。",
    }
    parts = [labels.get(signal, "")]
    if golden_cross:
        parts.append("（金叉：SMA50 在 SMA200 上方）")
    elif sma50 is not None and sma200 is not None and sma50 < sma200:
        parts.append("（死叉：SMA50 在 SMA200 下方）")
    if full_bull:
        parts.append("均线完美多头排列（SMA20>SMA50>SMA200）。")
    elif full_bear:
        parts.append("均线完美空头排列（SMA200>SMA50>SMA20）。")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_ma_alignment(ticker: str) -> MAAlignmentData:
    """Compute moving average alignment data for *ticker*.

    Never raises. Returns MAAlignmentData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1y", interval="1d")
    except Exception:
        return MAAlignmentData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    if hist.empty or "Close" not in hist.columns:
        return MAAlignmentData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算均线。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()

    if len(close) < 21:
        return MAAlignmentData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 21 个交易日，无法计算 SMA20。",
            as_of_date=as_of,
        )

    price = float(close.iloc[-1])

    # Compute SMAs where data allows
    sma20 = float(close.rolling(20).mean().iloc[-1]) if len(close) >= 20 else None
    sma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
    sma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None

    def dist(sma: float | None) -> float | None:
        if sma is None or sma <= 0:
            return None
        return (price - sma) / sma

    ma_score = _compute_ma_score(price, sma20, sma50, sma200)
    signal = _classify_signal(ma_score)

    golden_cross = sma50 is not None and sma200 is not None and sma50 > sma200
    full_bull = (
        sma20 is not None and sma50 is not None and sma200 is not None
        and price > sma20 > sma50 > sma200
    )
    full_bear = (
        sma20 is not None and sma50 is not None and sma200 is not None
        and sma200 > sma50 > sma20
        and price < sma20
    )

    interpretation = _build_interpretation(
        ticker, signal, ma_score, price,
        sma20, sma50, sma200,
        golden_cross, full_bull, full_bear,
    )

    return MAAlignmentData(
        ticker=ticker,
        price=round(price, 4),
        sma20=round(sma20, 4) if sma20 is not None else None,
        sma50=round(sma50, 4) if sma50 is not None else None,
        sma200=round(sma200, 4) if sma200 is not None else None,
        dist_from_20=dist(sma20),
        dist_from_50=dist(sma50),
        dist_from_200=dist(sma200),
        ma_score=round(ma_score, 1),
        golden_cross=golden_cross,
        full_bull_align=full_bull,
        full_bear_align=full_bear,
        signal=signal,
        interpretation=interpretation,
        as_of_date=as_of,
        data_available=True,
    )
