"""TRIX engine — Phase F.52.

Triple Exponential Average (TRIX):
  EMA1   = EMA(Close, 15)
  EMA2   = EMA(EMA1,  15)
  EMA3   = EMA(EMA2,  15)
  TRIX   = (EMA3[t] − EMA3[t−1]) / EMA3[t−1] × 100
  Signal = EMA(TRIX, 9)

Score = percentile rank of TRIX in last 252 bars × 100.

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

TRIXSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_TRIX_PERIOD  = 15
_SIGNAL_PERIOD = 9
_MIN_BARS      = 60   # 3 × 15 + buffer


@dataclass
class TRIXData:
    ticker: str
    trix: float | None = None            # Latest TRIX value (%)
    signal_line: float | None = None     # 9-period EMA of TRIX
    trix_positive: bool = False          # TRIX > 0
    trix_above_signal: bool = False      # TRIX > signal line (bullish)
    trix_score: float = 50.0            # 0-100 percentile-based score
    signal: TRIXSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_trix_series(
    close: pd.Series,
    period: int = _TRIX_PERIOD,
) -> tuple[pd.Series, pd.Series]:
    """Return (trix_series, signal_series).

    trix_series  = 1-period % change of EMA3.
    signal_series = EMA(trix, 9).
    """
    ema1 = close.ewm(span=period, adjust=False).mean()
    ema2 = ema1.ewm(span=period, adjust=False).mean()
    ema3 = ema2.ewm(span=period, adjust=False).mean()

    # % change of EMA3
    prev_ema3 = ema3.shift(1)
    trix = ((ema3 - prev_ema3) / prev_ema3.replace(0.0, float("nan"))) * 100.0
    trix = trix.fillna(0.0)

    sig = trix.ewm(span=_SIGNAL_PERIOD, adjust=False).mean()
    return trix, sig


def _compute_trix_score(
    trix_val: float,
    trix_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Percentile rank of trix_val within last *lookback* bars × 100."""
    window = trix_series.iloc[-lookback:].dropna()
    if len(window) < 10:
        return float(max(0.0, min(100.0, (trix_val + 1.0) / 2.0 * 100.0)))
    rank = float((window < trix_val).mean())
    return round(rank * 100.0, 1)


def _classify_signal(score: float | None) -> TRIXSignal:
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
    signal: TRIXSignal,
    trix: float,
    sig_line: float,
    score: float,
    above_signal: bool,
) -> str:
    cross = "TRIX 高于信号线（看涨）" if above_signal else "TRIX 低于信号线（看跌）"
    labels: dict[TRIXSignal, str] = {
        "strong_bull": (
            f"{ticker} TRIX {trix:+.4f}%（百分位 {score:.0f}），{cross}：三重平滑动量极强，趋势向上。"
        ),
        "bull": (
            f"{ticker} TRIX {trix:+.4f}%（百分位 {score:.0f}），{cross}：动量偏正，趋势偏强。"
        ),
        "neutral": (
            f"{ticker} TRIX {trix:+.4f}%（百分位 {score:.0f}），{cross}：动量中性，趋势横盘。"
        ),
        "bear": (
            f"{ticker} TRIX {trix:+.4f}%（百分位 {score:.0f}），{cross}：动量偏负，趋势偏弱。"
        ),
        "strong_bear": (
            f"{ticker} TRIX {trix:+.4f}%（百分位 {score:.0f}），{cross}：三重平滑动量极弱，趋势向下。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 TRIX。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_trix(ticker: str) -> TRIXData:
    """Compute TRIX data for *ticker*.

    Never raises. Returns TRIXData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return TRIXData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    if hist.empty or "Close" not in hist.columns:
        return TRIXData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 TRIX。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()

    if len(close) < _MIN_BARS:
        return TRIXData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 TRIX。",
            as_of_date=as_of,
        )

    trix_series, sig_series = _compute_trix_series(close)

    trix_val  = float(trix_series.iloc[-1])
    sig_val   = float(sig_series.iloc[-1])
    positive  = trix_val > 0.0
    above_sig = trix_val > sig_val

    score     = _compute_trix_score(trix_val, trix_series)
    signal    = _classify_signal(score)
    interp    = _build_interpretation(ticker, signal, trix_val, sig_val, score, above_sig)

    return TRIXData(
        ticker=ticker,
        trix=round(trix_val, 6),
        signal_line=round(sig_val, 6),
        trix_positive=positive,
        trix_above_signal=above_sig,
        trix_score=round(score, 1),
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
