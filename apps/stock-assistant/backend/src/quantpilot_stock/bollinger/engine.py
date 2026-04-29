"""Bollinger Band Squeeze engine — Phase F.38.

Computes Bollinger Bands (SMA20 ± 2σ), %B price position,
bandwidth, 6-month bandwidth percentile, squeeze state,
and composite bull/bear score (0-100).

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import yfinance as yf

BBSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]


@dataclass
class BollingerData:
    ticker: str
    price: float | None = None
    middle: float | None = None         # SMA20
    upper: float | None = None          # SMA20 + 2σ
    lower: float | None = None          # SMA20 − 2σ
    bandwidth: float | None = None      # (upper − lower) / middle × 100
    pct_b: float | None = None          # (price − lower) / (upper − lower)
    bandwidth_percentile: float | None = None   # 0-100: BW vs 6-month history
    squeeze_active: bool = False        # BW percentile < 20
    bb_score: float = 50.0              # 0-100
    signal: BBSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_MIN_BARS_BB = 20     # need at least 20 for SMA20/σ20
_PERCENTILE_BARS = 125  # ~6 months of trading days


def _compute_bb(
    close: "pd.Series",  # type: ignore[name-defined]  # noqa: F821
    period: int = 20,
    num_std: float = 2.0,
) -> tuple[float, float, float, float, float]:
    """Return (price, middle, upper, lower, bandwidth) for latest bar."""
    sma = close.rolling(period).mean()
    std = close.rolling(period).std(ddof=0)

    middle = float(sma.iloc[-1])
    sigma = float(std.iloc[-1])
    upper = middle + num_std * sigma
    lower = middle - num_std * sigma
    price = float(close.iloc[-1])

    if middle > 0:
        bandwidth = (upper - lower) / middle * 100.0
    else:
        bandwidth = 0.0

    return price, middle, upper, lower, bandwidth


def _compute_bandwidth_percentile(
    close: "pd.Series",  # type: ignore[name-defined]  # noqa: F821
    period: int = 20,
    num_std: float = 2.0,
    lookback: int = _PERCENTILE_BARS,
) -> float | None:
    """Percentile of current bandwidth vs *lookback* bars of history."""
    sma = close.rolling(period).mean()
    std = close.rolling(period).std(ddof=0)

    upper_s = sma + num_std * std
    lower_s = sma - num_std * std
    bw_series = (upper_s - lower_s) / sma.replace(0, float("nan")) * 100.0
    bw_valid = bw_series.dropna()

    if len(bw_valid) < 2:
        return None

    history = bw_valid.iloc[-lookback:]
    current_bw = float(bw_valid.iloc[-1])
    pct = float((history < current_bw).mean() * 100.0)
    return round(pct, 1)


def _compute_pct_b(price: float, upper: float, lower: float) -> float | None:
    band_width = upper - lower
    if band_width <= 0:
        return None
    return (price - lower) / band_width


def _compute_bb_score(
    pct_b: float | None,
    bandwidth_percentile: float | None,
) -> float:
    """Composite BB score in [0, 100].

    Primary signal from %B:
      pct_b >= 0.9  → raw +3 (price above upper band or very near top)
      pct_b >= 0.7  → raw +2
      pct_b >= 0.5  → raw +1
      pct_b >= 0.3  → raw -1
      pct_b >= 0.1  → raw -2
      pct_b <  0.1  → raw -3 (price at/below lower band)

    Bandwidth bonus (trend confirmation):
      BW percentile >= 70 and price above middle → +1 (high vol + bull)
      BW percentile >= 70 and price below middle → -1 (high vol + bear)
      BW percentile < 20 (squeeze) → 0 (direction unclear)

    Raw range: [-4, 4] → mapped to [0, 100].
    """
    raw = 0.0

    if pct_b is not None:
        if pct_b >= 0.9:
            raw += 3.0
        elif pct_b >= 0.7:
            raw += 2.0
        elif pct_b >= 0.5:
            raw += 1.0
        elif pct_b >= 0.3:
            raw -= 1.0
        elif pct_b >= 0.1:
            raw -= 2.0
        else:
            raw -= 3.0

    if bandwidth_percentile is not None and pct_b is not None:
        if bandwidth_percentile >= 70:
            raw += 1.0 if pct_b >= 0.5 else -1.0

    # Map [-4, 4] → [0, 100]
    normalized = (raw + 4.0) / 8.0 * 100.0
    return float(max(0.0, min(100.0, normalized)))


def _classify_signal(bb_score: float | None) -> BBSignal:
    if bb_score is None:
        return "no_data"
    if bb_score >= 80:
        return "strong_bull"
    if bb_score >= 60:
        return "bull"
    if bb_score >= 40:
        return "neutral"
    if bb_score >= 20:
        return "bear"
    return "strong_bear"


def _build_interpretation(
    ticker: str,
    signal: BBSignal,
    bb_score: float,
    pct_b: float | None,
    bandwidth_percentile: float | None,
    squeeze_active: bool,
) -> str:
    labels: dict[BBSignal, str] = {
        "strong_bull": (
            f"{ticker} 布林评分 {bb_score:.0f}：价格接近或突破上轨，强势看涨。"
        ),
        "bull": (
            f"{ticker} 布林评分 {bb_score:.0f}：价格在中轨上方偏上，偏多头。"
        ),
        "neutral": (
            f"{ticker} 布林评分 {bb_score:.0f}：价格在布林中轨附近，中性整理。"
        ),
        "bear": (
            f"{ticker} 布林评分 {bb_score:.0f}：价格在中轨下方偏下，偏空头。"
        ),
        "strong_bear": (
            f"{ticker} 布林评分 {bb_score:.0f}：价格接近或跌破下轨，强势看跌。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算布林带。",
    }
    parts = [labels.get(signal, "")]
    if squeeze_active:
        parts.append("（布林带收缩中，波动率压缩，等待方向性突破）")
    elif bandwidth_percentile is not None and bandwidth_percentile >= 80:
        parts.append("（布林带已扩张，当前处于高波动状态）")
    if pct_b is not None:
        parts.append(f"（%B = {pct_b:.2f}）")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_bollinger(ticker: str) -> BollingerData:
    """Compute Bollinger Band data for *ticker*.

    Never raises. Returns BollingerData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1y", interval="1d")
    except Exception:
        return BollingerData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    if hist.empty or "Close" not in hist.columns:
        return BollingerData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算布林带。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()

    if len(close) < _MIN_BARS_BB:
        return BollingerData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS_BB} 个交易日，无法计算布林带。",
            as_of_date=as_of,
        )

    price, middle, upper, lower, bandwidth = _compute_bb(close)
    pct_b = _compute_pct_b(price, upper, lower)
    bandwidth_percentile = _compute_bandwidth_percentile(close)
    squeeze_active = bandwidth_percentile is not None and bandwidth_percentile < 20.0

    bb_score = _compute_bb_score(pct_b, bandwidth_percentile)
    signal = _classify_signal(bb_score)

    interpretation = _build_interpretation(
        ticker, signal, bb_score, pct_b, bandwidth_percentile, squeeze_active
    )

    return BollingerData(
        ticker=ticker,
        price=round(price, 4),
        middle=round(middle, 4),
        upper=round(upper, 4),
        lower=round(lower, 4),
        bandwidth=round(bandwidth, 2),
        pct_b=round(pct_b, 4) if pct_b is not None else None,
        bandwidth_percentile=bandwidth_percentile,
        squeeze_active=squeeze_active,
        bb_score=round(bb_score, 1),
        signal=signal,
        interpretation=interpretation,
        as_of_date=as_of,
        data_available=True,
    )
