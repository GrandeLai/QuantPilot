"""Chande Kroll Stop (CKS) engine — Phase F.72.

CKS Formula (Chande & Kroll, "The New Technical Trader", 1994):

  ATR_p    = ATR(atr_period)
  First_H  = High.rolling(p).max() − coeff × ATR_p
  First_L  = Low.rolling(p).min()  + coeff × ATR_p
  Stop_S   = First_H.rolling(q).max()   (upper/bull stop)
  Stop_L   = First_L.rolling(q).min()   (lower/bear stop)

  Defaults: p=10, q=9, coeff=1

  Signal:
    price > Stop_S  → bullish (above bull stop)
    price < Stop_L  → bearish (below bear stop)
    between         → neutral

Score (0–100):
  40 pts  close > stop_short (above bull stop)
  30 pts  stop_short rising  (stop_short[n] > stop_short[n−3])
  30 pts  (close − stop_short) / close percentile in 252-bar window × 30

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

CKSSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_P     = 10
_Q     = 9
_COEFF = 1.0
_MIN_BARS = _P + _Q + 5


@dataclass
class CKSData:
    ticker: str
    stop_short: float | None = None    # bull stop level
    stop_long: float | None = None     # bear stop level
    close_value: float | None = None
    price_above_stop: bool | None = None
    stop_rising: bool | None = None
    cks_score: float = 50.0
    signal: CKSSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int) -> pd.Series:
    """Average True Range."""
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


def _compute_cks_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    p: int = _P,
    q: int = _Q,
    coeff: float = _COEFF,
) -> tuple[pd.Series, pd.Series]:
    """Return (stop_short, stop_long) series."""
    atr      = _compute_atr(high, low, close, p)
    first_h  = high.rolling(p).max() - coeff * atr
    first_l  = low.rolling(p).min()  + coeff * atr
    stop_s   = first_h.rolling(q).max().ffill().fillna(close)
    stop_l   = first_l.rolling(q).min().ffill().fillna(close)
    return stop_s, stop_l


def _compute_cks_score(
    close_val: float,
    stop_s_val: float,
    stop_s_series: pd.Series,
    close_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Composite score 0–100."""
    above_pts = 40.0 if close_val > stop_s_val else 0.0

    recent = stop_s_series.dropna()
    if len(recent) >= 4:
        slope_pts = 30.0 if float(recent.iloc[-1]) > float(recent.iloc[-4]) else 0.0
    else:
        slope_pts = 15.0

    # Percentile rank of (close - stop_s) / close
    ratio_s = ((close_series - stop_s_series) / close_series.replace(0, float("nan"))).dropna()
    window  = ratio_s.iloc[-lookback:]
    current = (close_val - stop_s_val) / close_val if close_val != 0 else 0.0
    if len(window) < 10:
        pct_pts = 15.0
    else:
        pct_pts = float((window < current).mean()) * 30.0

    return round(above_pts + slope_pts + pct_pts, 1)


def _classify_signal(score: float | None) -> CKSSignal:
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
    signal: CKSSignal,
    close_val: float,
    stop_s: float,
    stop_l: float,
    above: bool,
    rising: bool,
    score: float,
) -> str:
    pos_str   = "高于" if above else "低于"
    trend_str = "上升" if rising else "下降"
    labels: dict[CKSSignal, str] = {
        "strong_bull": (
            f"{ticker} 收盘价={close_val:.2f}，{pos_str}多头止损({stop_s:.2f})，"
            f"止损线{trend_str}（得分 {score:.0f}）：价格远在止损线上方，趋势极强。"
        ),
        "bull": (
            f"{ticker} 收盘价={close_val:.2f}，{pos_str}多头止损({stop_s:.2f})，"
            f"止损线{trend_str}（得分 {score:.0f}）：价格在止损线上方，趋势偏强。"
        ),
        "neutral": (
            f"{ticker} 收盘价={close_val:.2f}，{pos_str}多头止损({stop_s:.2f})，"
            f"止损线{trend_str}（得分 {score:.0f}）：价格在止损区间内，趋势不明。"
        ),
        "bear": (
            f"{ticker} 收盘价={close_val:.2f}，{pos_str}多头止损({stop_s:.2f})，"
            f"止损线{trend_str}（得分 {score:.0f}）：价格低于止损线，趋势偏弱。"
        ),
        "strong_bear": (
            f"{ticker} 收盘价={close_val:.2f}，{pos_str}多头止损({stop_s:.2f})，空头止损({stop_l:.2f})，"
            f"止损线{trend_str}（得分 {score:.0f}）：价格在空头止损线以下，趋势极弱。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 CKS 指标。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_cks(ticker: str) -> CKSData:
    """Compute Chande Kroll Stop for *ticker*.

    Never raises. Returns CKSData with data_available=False on failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return CKSData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    required = {"High", "Low", "Close"}
    if hist.empty or not required.issubset(hist.columns):
        return CKSData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 CKS。",
            as_of_date=as_of,
        )

    close  = hist["Close"].dropna()
    idx    = close.index
    high   = hist["High"].loc[idx].fillna(close)
    low    = hist["Low"].loc[idx].fillna(close)

    if len(close) < _MIN_BARS:
        return CKSData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 CKS。",
            as_of_date=as_of,
        )

    stop_s_s, stop_l_s = _compute_cks_series(high, low, close)

    close_val   = float(close.iloc[-1])
    stop_s_val  = float(stop_s_s.iloc[-1])
    stop_l_val  = float(stop_l_s.iloc[-1])

    recent      = stop_s_s.dropna()
    stop_rising = bool(len(recent) >= 4 and float(recent.iloc[-1]) > float(recent.iloc[-4]))

    score  = _compute_cks_score(close_val, stop_s_val, stop_s_s, close)
    signal = _classify_signal(score)
    interp = _build_interpretation(
        ticker, signal, close_val, stop_s_val, stop_l_val,
        close_val > stop_s_val, stop_rising, score,
    )

    return CKSData(
        ticker=ticker,
        stop_short=round(stop_s_val, 4),
        stop_long=round(stop_l_val, 4),
        close_value=round(close_val, 4),
        price_above_stop=close_val > stop_s_val,
        stop_rising=stop_rising,
        cks_score=score,
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
