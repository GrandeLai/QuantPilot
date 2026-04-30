"""Ichimoku Kinko Hyo engine — Phase F.59.

Tenkan-sen (9)  = midpoint of 9-bar high/low range
Kijun-sen (26)  = midpoint of 26-bar high/low range
Senkou A        = (Tenkan + Kijun) / 2  (current bar value)
Senkou B (52)   = midpoint of 52-bar high/low range
Chikou Span     = Close[today] vs Close[26 bars ago]

Score (0–100):
  40 pts  price vs cloud (above → 40, inside → 20, below → 0)
  30 pts  Tenkan vs Kijun (Tenkan > Kijun → 30, else → 0)
  30 pts  cloud color (Senkou A > Senkou B → 30, else → 0)

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

IchimokuSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_TENKAN  = 9
_KIJUN   = 26
_SENKOU_B = 52
_MIN_BARS = _SENKOU_B + 5


@dataclass
class IchimokuData:
    ticker: str
    tenkan: float | None = None          # Conversion line
    kijun: float | None = None           # Base line
    senkou_a: float | None = None        # Leading span A
    senkou_b: float | None = None        # Leading span B
    chikou_above: bool | None = None     # Chikou above close 26 bars ago
    price_vs_cloud: str = "inside"       # "above" | "inside" | "below"
    cloud_bullish: bool | None = None    # Senkou A > Senkou B
    tk_bullish: bool | None = None       # Tenkan > Kijun
    ichimoku_score: float = 50.0        # 0–100 composite
    signal: IchimokuSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _midpoint(high: pd.Series, low: pd.Series, period: int) -> pd.Series:
    """(rolling_max_high + rolling_min_low) / 2."""
    return (high.rolling(period).max() + low.rolling(period).min()) / 2.0


def _compute_ichimoku_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """Return (tenkan, kijun, senkou_a, senkou_b)."""
    tenkan  = _midpoint(high, low, _TENKAN)
    kijun   = _midpoint(high, low, _KIJUN)
    senkou_a = (tenkan + kijun) / 2.0
    senkou_b = _midpoint(high, low, _SENKOU_B)
    return tenkan, kijun, senkou_a, senkou_b


def _compute_ichimoku_score(
    close_val: float,
    tenkan_val: float,
    kijun_val: float,
    senkou_a_val: float,
    senkou_b_val: float,
) -> tuple[float, str, bool, bool]:
    """Return (score, price_vs_cloud, cloud_bullish, tk_bullish)."""
    cloud_top    = max(senkou_a_val, senkou_b_val)
    cloud_bottom = min(senkou_a_val, senkou_b_val)

    if close_val > cloud_top:
        price_pts     = 40.0
        price_vs_cloud = "above"
    elif close_val < cloud_bottom:
        price_pts     = 0.0
        price_vs_cloud = "below"
    else:
        price_pts     = 20.0
        price_vs_cloud = "inside"

    tk_bullish    = tenkan_val > kijun_val
    tk_pts        = 30.0 if tk_bullish else 0.0

    cloud_bullish = senkou_a_val > senkou_b_val
    cloud_pts     = 30.0 if cloud_bullish else 0.0

    score = price_pts + tk_pts + cloud_pts
    return round(score, 1), price_vs_cloud, cloud_bullish, tk_bullish


def _classify_signal(score: float | None) -> IchimokuSignal:
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
    signal: IchimokuSignal,
    price_vs_cloud: str,
    cloud_bullish: bool,
    tk_bullish: bool,
    score: float,
) -> str:
    cloud_str = "多头云" if cloud_bullish else "空头云"
    tk_str    = "转换线上方基准线（多头排列）" if tk_bullish else "转换线下方基准线（空头排列）"
    pos_str   = {"above": "云层上方", "inside": "云层内部", "below": "云层下方"}.get(price_vs_cloud, "")
    labels: dict[IchimokuSignal, str] = {
        "strong_bull": (
            f"{ticker} 价格处于{pos_str}（得分 {score:.0f}），{cloud_str}，{tk_str}：多重看涨确认，极强趋势。"
        ),
        "bull": (
            f"{ticker} 价格处于{pos_str}（得分 {score:.0f}），{cloud_str}，{tk_str}：偏强看涨倾向。"
        ),
        "neutral": (
            f"{ticker} 价格处于{pos_str}（得分 {score:.0f}），{cloud_str}，{tk_str}：一云图信号中性混杂。"
        ),
        "bear": (
            f"{ticker} 价格处于{pos_str}（得分 {score:.0f}），{cloud_str}，{tk_str}：偏弱看跌倾向。"
        ),
        "strong_bear": (
            f"{ticker} 价格处于{pos_str}（得分 {score:.0f}），{cloud_str}，{tk_str}：多重看跌确认，极弱趋势。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算一云图指标。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_ichimoku(ticker: str) -> IchimokuData:
    """Compute Ichimoku Kinko Hyo for *ticker*.

    Never raises. Returns IchimokuData with data_available=False on failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return IchimokuData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    required = {"High", "Low", "Close"}
    if hist.empty or not required.issubset(hist.columns):
        return IchimokuData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算一云图。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()
    high  = hist["High"].loc[close.index].dropna()
    low   = hist["Low"].loc[close.index].dropna()

    common = close.index.intersection(high.index).intersection(low.index)
    close, high, low = close.loc[common], high.loc[common], low.loc[common]

    if len(close) < _MIN_BARS:
        return IchimokuData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算一云图。",
            as_of_date=as_of,
        )

    tenkan_s, kijun_s, senkou_a_s, senkou_b_s = _compute_ichimoku_series(high, low, close)

    tenkan_val   = float(tenkan_s.iloc[-1])
    kijun_val    = float(kijun_s.iloc[-1])
    senkou_a_val = float(senkou_a_s.iloc[-1])
    senkou_b_val = float(senkou_b_s.iloc[-1])
    close_val    = float(close.iloc[-1])

    # Chikou: compare today's close vs close 26 bars ago
    chikou_above: bool | None = None
    if len(close) >= _KIJUN + 1:
        past_close    = float(close.iloc[-(_KIJUN + 1)])
        chikou_above  = close_val > past_close

    score, price_vs_cloud, cloud_bullish, tk_bullish = _compute_ichimoku_score(
        close_val, tenkan_val, kijun_val, senkou_a_val, senkou_b_val,
    )

    signal = _classify_signal(score)
    interp = _build_interpretation(ticker, signal, price_vs_cloud, cloud_bullish, tk_bullish, score)

    return IchimokuData(
        ticker=ticker,
        tenkan=round(tenkan_val, 4),
        kijun=round(kijun_val, 4),
        senkou_a=round(senkou_a_val, 4),
        senkou_b=round(senkou_b_val, 4),
        chikou_above=chikou_above,
        price_vs_cloud=price_vs_cloud,
        cloud_bullish=cloud_bullish,
        tk_bullish=tk_bullish,
        ichimoku_score=score,
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
