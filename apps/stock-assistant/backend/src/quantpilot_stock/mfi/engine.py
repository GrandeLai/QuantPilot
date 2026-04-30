"""Money Flow Index (MFI) engine — Phase F.42.

MFI = 100 - 100 / (1 + Positive_Money_Flow / Negative_Money_Flow)
over a 14-period window.  Volume-weighted RSI analogue.

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import numpy as np
import pandas as pd
import yfinance as yf

MFISignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]


@dataclass
class MFIData:
    ticker: str
    mfi: float | None = None              # Latest MFI value (0-100)
    prev_mfi: float | None = None         # Previous bar MFI (for direction)
    mfi_direction: str = ""               # "rising" | "falling" | "flat"
    overbought: bool = False              # MFI >= 80
    oversold: bool = False                # MFI <= 20
    bullish_divergence: bool = False      # Price making new low, MFI not
    bearish_divergence: bool = False      # Price making new high, MFI not
    mfi_score: float = 50.0              # 0-100 composite score
    signal: MFISignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_MIN_BARS = 30   # 14 (MFI period) + 14 (lookback for divergence) + guard


def _compute_mfi_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Return MFI series in [0, 100]."""
    tp = (high + low + close) / 3.0
    rmf = tp * volume.astype(float)

    delta_tp = tp.diff()

    positive_mf = pd.Series(np.where(delta_tp > 0, rmf, 0.0), index=tp.index)
    negative_mf = pd.Series(np.where(delta_tp < 0, rmf, 0.0), index=tp.index)

    pmf_sum = positive_mf.rolling(period).sum()
    nmf_sum = negative_mf.rolling(period).sum()

    # Edge cases:
    #   nmf=0, pmf>0 → MFI=100 (all money positive)
    #   nmf=0, pmf=0 → MFI=50  (no money flow)
    #   pmf=0, nmf>0 → MFI=0   (all money negative)
    with np.errstate(divide="ignore", invalid="ignore"):
        mfr = np.where(
            nmf_sum == 0,
            np.where(pmf_sum == 0, 1.0, np.inf),  # 1→MFI=50, inf→MFI=100
            pmf_sum.values / nmf_sum.values,
        )
    mfi = pd.Series(100.0 - (100.0 / (1.0 + mfr)), index=pmf_sum.index)
    return mfi.fillna(50.0)  # initial rolling window → neutral


def _detect_mfi_divergence(
    close: pd.Series,
    mfi_series: pd.Series,
    lookback: int = 20,
) -> tuple[bool, bool]:
    """Detect bullish / bearish MFI divergence over the last *lookback* bars.

    Bullish: price lower low, MFI higher low.
    Bearish: price higher high, MFI lower high.
    """
    if len(close) < lookback or len(mfi_series) < lookback:
        return False, False

    c = close.iloc[-lookback:]
    m = mfi_series.iloc[-lookback:]

    mid = lookback // 2
    c_first = c.iloc[:mid]
    c_last = c.iloc[mid:]
    m_first = m.iloc[:mid]
    m_last = m.iloc[mid:]

    bullish = float(c_last.min()) < float(c_first.min()) and float(m_last.min()) > float(m_first.min())
    bearish = float(c_last.max()) > float(c_first.max()) and float(m_last.max()) < float(m_first.max())
    return bullish, bearish


def _compute_mfi_score(
    mfi: float,
    bullish_divergence: bool,
    bearish_divergence: bool,
) -> float:
    """Composite MFI score in [0, 100].

    Base score = MFI value (already 0-100).
    Adjustments:
      +8  bullish divergence
      -8  bearish divergence
    Clipped to [0, 100].
    """
    base = mfi
    if bullish_divergence:
        base += 8.0
    if bearish_divergence:
        base -= 8.0
    return float(max(0.0, min(100.0, base)))


def _classify_signal(mfi_score: float | None) -> MFISignal:
    if mfi_score is None:
        return "no_data"
    if mfi_score >= 80:
        return "strong_bull"
    if mfi_score >= 60:
        return "bull"
    if mfi_score >= 40:
        return "neutral"
    if mfi_score >= 20:
        return "bear"
    return "strong_bear"


def _build_interpretation(
    ticker: str,
    signal: MFISignal,
    mfi: float,
    overbought: bool,
    oversold: bool,
    bullish_divergence: bool,
    bearish_divergence: bool,
) -> str:
    labels: dict[MFISignal, str] = {
        "strong_bull": f"{ticker} MFI {mfi:.1f}：资金流入强势，超买区间，动量充足。",
        "bull": f"{ticker} MFI {mfi:.1f}：资金流入偏多，买盘力量占优。",
        "neutral": f"{ticker} MFI {mfi:.1f}：资金流向均衡，多空力量相当。",
        "bear": f"{ticker} MFI {mfi:.1f}：资金流出偏空，卖盘占优。",
        "strong_bear": f"{ticker} MFI {mfi:.1f}：资金流出强势，超卖区间或持续流出。",
        "no_data": f"{ticker} 数据不足，无法计算 MFI。",
    }
    parts = [labels.get(signal, "")]
    if overbought:
        parts.append("（MFI ≥ 80，资金超买，注意回调风险）")
    elif oversold:
        parts.append("（MFI ≤ 20，资金超卖，关注反弹机会）")
    if bullish_divergence:
        parts.append("（价格新低但 MFI 未新低，量能背离看涨）")
    if bearish_divergence:
        parts.append("（价格新高但 MFI 未新高，量能背离看跌）")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_mfi(ticker: str) -> MFIData:
    """Compute MFI data for *ticker*.

    Never raises. Returns MFIData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1y", interval="1d")
    except Exception:
        return MFIData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    required = {"High", "Low", "Close", "Volume"}
    if hist.empty or not required.issubset(hist.columns):
        return MFIData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 MFI。",
            as_of_date=as_of,
        )

    high = hist["High"].dropna()
    low = hist["Low"].dropna()
    close = hist["Close"].dropna()
    volume = hist["Volume"].dropna()

    common_idx = high.index.intersection(low.index).intersection(close.index).intersection(volume.index)
    high = high.loc[common_idx]
    low = low.loc[common_idx]
    close = close.loc[common_idx]
    volume = volume.loc[common_idx]

    if len(close) < _MIN_BARS:
        return MFIData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 MFI。",
            as_of_date=as_of,
        )

    mfi_series = _compute_mfi_series(high, low, close, volume)

    mfi_val = float(mfi_series.iloc[-1])
    prev_mfi = float(mfi_series.iloc[-2]) if len(mfi_series) >= 2 else None

    if prev_mfi is not None:
        if mfi_val > prev_mfi + 0.5:
            direction = "rising"
        elif mfi_val < prev_mfi - 0.5:
            direction = "falling"
        else:
            direction = "flat"
    else:
        direction = "flat"

    overbought = mfi_val >= 80.0
    oversold = mfi_val <= 20.0

    bull_div, bear_div = _detect_mfi_divergence(close, mfi_series)

    mfi_score = _compute_mfi_score(mfi_val, bull_div, bear_div)
    signal = _classify_signal(mfi_score)
    interpretation = _build_interpretation(
        ticker, signal, mfi_val, overbought, oversold, bull_div, bear_div
    )

    return MFIData(
        ticker=ticker,
        mfi=round(mfi_val, 2),
        prev_mfi=round(prev_mfi, 2) if prev_mfi is not None else None,
        mfi_direction=direction,
        overbought=overbought,
        oversold=oversold,
        bullish_divergence=bull_div,
        bearish_divergence=bear_div,
        mfi_score=round(mfi_score, 1),
        signal=signal,
        interpretation=interpretation,
        as_of_date=as_of,
        data_available=True,
    )
