"""Chaikin Volatility (CV) engine — Phase F.74.

CV Formula (Marc Chaikin):
  HL        = High − Low
  EMA_HL    = EMA(ema_period, HL)
  CV        = (EMA_HL − EMA_HL.shift(roc_period)) / EMA_HL.shift(roc_period) × 100

  Defaults: ema_period=10, roc_period=10

  Interpretation:
    CV rising    → expanding volatility (trend continuation / breakout)
    CV falling   → contracting volatility (consolidation / potential reversal)
    CV near zero → stable volatility

Score (0–100):
  This is a volatility indicator, not a directional one.
  We score based on the DIRECTION of price combined with CV:
  35 pts  CV < 0  (volatility contracting → lower-risk to hold trend)
  35 pts  price momentum positive (close > 10-period SMA)
  30 pts  percentile rank of price momentum in 252-bar window × 30

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

CVSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_EMA_PERIOD = 10
_ROC_PERIOD = 10
_TREND_SMA  = 10
_MIN_BARS   = _EMA_PERIOD + _ROC_PERIOD + _TREND_SMA + 5


@dataclass
class CVData:
    ticker: str
    cv_value: float | None = None
    vol_expanding: bool | None = None     # CV > 0
    price_above_sma: bool | None = None   # close > SMA(10)
    cv_score: float = 50.0
    signal: CVSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_cv_series(
    high: pd.Series,
    low: pd.Series,
    ema_period: int = _EMA_PERIOD,
    roc_period: int = _ROC_PERIOD,
) -> pd.Series:
    """Return Chaikin Volatility series."""
    hl       = (high - low).clip(lower=0.0)
    ema_hl   = hl.ewm(span=ema_period, adjust=False).mean()
    prev_ema = ema_hl.shift(roc_period)
    cv       = ((ema_hl - prev_ema) / prev_ema.replace(0, float("nan")) * 100).fillna(0.0)
    return cv


def _compute_cv_score(
    cv_val: float,
    close_val: float,
    sma_val: float,
    momentum_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Composite score 0–100."""
    contract_pts = 35.0 if cv_val < 0 else 0.0
    above_pts    = 35.0 if close_val > sma_val else 0.0

    window  = momentum_series.dropna().iloc[-lookback:]
    current = (close_val - sma_val) / sma_val if sma_val != 0 else 0.0
    if len(window) < 10:
        pct_pts = 15.0
    else:
        pct_pts = float((window < current).mean()) * 30.0

    return round(contract_pts + above_pts + pct_pts, 1)


def _classify_signal(score: float | None) -> CVSignal:
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
    signal: CVSignal,
    cv_val: float,
    expanding: bool,
    above_sma: bool,
    score: float,
) -> str:
    vol_str = "波动率扩张" if expanding else "波动率收缩"
    trend_str = "高于" if above_sma else "低于"
    labels: dict[CVSignal, str] = {
        "strong_bull": (
            f"{ticker} CV={cv_val:.2f}%，{vol_str}，价格{trend_str}SMA(10)（得分 {score:.0f}）：价格在均线上方且波动收缩，适合持有多头。"
        ),
        "bull": (
            f"{ticker} CV={cv_val:.2f}%，{vol_str}，价格{trend_str}SMA(10)（得分 {score:.0f}）：价格动能偏强，波动适中。"
        ),
        "neutral": (
            f"{ticker} CV={cv_val:.2f}%，{vol_str}，价格{trend_str}SMA(10)（得分 {score:.0f}）：波动率中性，趋势待确认。"
        ),
        "bear": (
            f"{ticker} CV={cv_val:.2f}%，{vol_str}，价格{trend_str}SMA(10)（得分 {score:.0f}）：价格动能偏弱，注意风险。"
        ),
        "strong_bear": (
            f"{ticker} CV={cv_val:.2f}%，{vol_str}，价格{trend_str}SMA(10)（得分 {score:.0f}）：波动扩张叠加价格弱势，下行风险高。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 Chaikin 波动率。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_cv(ticker: str) -> CVData:
    """Compute Chaikin Volatility for *ticker*.

    Never raises. Returns CVData with data_available=False on failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return CVData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    required = {"High", "Low", "Close"}
    if hist.empty or not required.issubset(hist.columns):
        return CVData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 CV。",
            as_of_date=as_of,
        )

    close  = hist["Close"].dropna()
    idx    = close.index
    high   = hist["High"].loc[idx].fillna(close)
    low    = hist["Low"].loc[idx].fillna(close)

    if len(close) < _MIN_BARS:
        return CVData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 CV。",
            as_of_date=as_of,
        )

    cv_s    = _compute_cv_series(high, low)
    sma_s   = close.rolling(_TREND_SMA).mean().fillna(close)

    # Momentum ratio series for percentile
    momentum_s = ((close - sma_s) / sma_s.replace(0, float("nan"))).fillna(0.0)

    cv_val    = float(cv_s.iloc[-1])
    close_val = float(close.iloc[-1])
    sma_val   = float(sma_s.iloc[-1])

    score  = _compute_cv_score(cv_val, close_val, sma_val, momentum_s)
    signal = _classify_signal(score)
    interp = _build_interpretation(
        ticker, signal, cv_val, cv_val > 0, close_val > sma_val, score
    )

    return CVData(
        ticker=ticker,
        cv_value=round(cv_val, 2),
        vol_expanding=cv_val > 0,
        price_above_sma=close_val > sma_val,
        cv_score=score,
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
