"""Know Sure Thing (KST) engine — Phase F.60.

KST aggregates Rate-of-Change across 4 timeframes, smoothed and weighted:

  ROC(n)  = (close / close.shift(n) - 1) * 100
  RCMA1   = SMA(10, ROC(10))
  RCMA2   = SMA(10, ROC(15))
  RCMA3   = SMA(10, ROC(20))
  RCMA4   = SMA(15, ROC(30))
  KST     = RCMA1*1 + RCMA2*2 + RCMA3*3 + RCMA4*4
  Signal  = SMA(9, KST)

Score (0–100):
  40 pts  KST > 0 (bullish zero-line position)
  30 pts  KST > Signal (bullish cross)
  30 pts  percentile rank of KST in 252-bar window × 30

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

KSTSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_MIN_BARS = 30 + 15 + 10 + 5  # ROC(30) + RCMA4 SMA(15) + signal SMA(9) buffer


@dataclass
class KSTData:
    ticker: str
    kst_value: float | None = None         # Current KST value
    signal_line: float | None = None       # SMA(9) of KST
    kst_positive: bool | None = None       # KST > 0
    kst_above_signal: bool | None = None   # KST > signal
    kst_score: float = 50.0               # 0–100 composite
    signal: KSTSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _roc(close: pd.Series, n: int) -> pd.Series:
    """Rate of change in percent."""
    shifted = close.shift(n)
    return (close / shifted - 1.0) * 100.0


def _compute_kst_series(
    close: pd.Series,
) -> tuple[pd.Series, pd.Series]:
    """Return (kst, signal) series."""
    rcma1 = _roc(close, 10).rolling(10).mean()
    rcma2 = _roc(close, 15).rolling(10).mean()
    rcma3 = _roc(close, 20).rolling(10).mean()
    rcma4 = _roc(close, 30).rolling(15).mean()

    kst    = rcma1 * 1 + rcma2 * 2 + rcma3 * 3 + rcma4 * 4
    signal = kst.rolling(9).mean()
    return kst.ffill().fillna(0.0), signal.ffill().fillna(0.0)


def _compute_kst_score(
    kst_val: float,
    sig_val: float,
    kst_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Composite score 0–100."""
    zero_pts   = 40.0 if kst_val > 0 else 0.0
    signal_pts = 30.0 if kst_val > sig_val else 0.0

    window = kst_series.iloc[-lookback:].dropna()
    if len(window) < 10:
        pct_pts = 15.0
    else:
        pct_pts = float((window < kst_val).mean()) * 30.0

    return round(zero_pts + signal_pts + pct_pts, 1)


def _classify_signal(score: float | None) -> KSTSignal:
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
    signal: KSTSignal,
    kst_val: float,
    sig_val: float,
    score: float,
) -> str:
    pos_str = "零线上方（多头）" if kst_val > 0 else "零线下方（空头）"
    cross_str = "高于信号线（金叉）" if kst_val > sig_val else "低于信号线（死叉）"
    labels: dict[KSTSignal, str] = {
        "strong_bull": (
            f"{ticker} KST={kst_val:.2f} 处于{pos_str}，{cross_str}（得分 {score:.0f}）：多周期动量极强。"
        ),
        "bull": (
            f"{ticker} KST={kst_val:.2f} 处于{pos_str}，{cross_str}（得分 {score:.0f}）：多周期动量偏强。"
        ),
        "neutral": (
            f"{ticker} KST={kst_val:.2f} 处于{pos_str}，{cross_str}（得分 {score:.0f}）：多周期动量中性。"
        ),
        "bear": (
            f"{ticker} KST={kst_val:.2f} 处于{pos_str}，{cross_str}（得分 {score:.0f}）：多周期动量偏弱。"
        ),
        "strong_bear": (
            f"{ticker} KST={kst_val:.2f} 处于{pos_str}，{cross_str}（得分 {score:.0f}）：多周期动量极弱。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 KST 指标。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_kst(ticker: str) -> KSTData:
    """Compute KST for *ticker*.

    Never raises. Returns KSTData with data_available=False on failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return KSTData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    if hist.empty or "Close" not in hist.columns:
        return KSTData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 KST。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()

    if len(close) < _MIN_BARS:
        return KSTData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 KST。",
            as_of_date=as_of,
        )

    kst_s, sig_s = _compute_kst_series(close)

    kst_val = float(kst_s.iloc[-1])
    sig_val = float(sig_s.iloc[-1])

    score  = _compute_kst_score(kst_val, sig_val, kst_s)
    signal = _classify_signal(score)
    interp = _build_interpretation(ticker, signal, kst_val, sig_val, score)

    return KSTData(
        ticker=ticker,
        kst_value=round(kst_val, 4),
        signal_line=round(sig_val, 4),
        kst_positive=kst_val > 0,
        kst_above_signal=kst_val > sig_val,
        kst_score=score,
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
