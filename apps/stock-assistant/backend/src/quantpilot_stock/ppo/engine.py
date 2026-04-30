"""Percentage Price Oscillator (PPO) engine — Phase F.66.

  PPO       = (EMA(12) − EMA(26)) / EMA(26) × 100
  Signal    = EMA(9, PPO)
  Histogram = PPO − Signal

Score (0–100):
  35 pts  PPO > Signal (momentum crossover zone)
  35 pts  PPO > 0     (fast EMA above slow EMA)
  30 pts  percentile rank of PPO in 252-bar window × 30

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

PPOSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_FAST_PERIOD   = 12
_SLOW_PERIOD   = 26
_SIGNAL_PERIOD = 9
_MIN_BARS      = _SLOW_PERIOD + _SIGNAL_PERIOD + 5


@dataclass
class PPOData:
    ticker: str
    ppo_value: float | None = None          # percentage (e.g. 1.5 means 1.5 %)
    signal_value: float | None = None       # EMA(9, PPO)
    histogram: float | None = None          # PPO − Signal
    ppo_above_signal: bool | None = None
    ppo_positive: bool | None = None        # PPO > 0
    ppo_score: float = 50.0                 # 0–100 composite
    signal: PPOSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_ppo_series(
    close: pd.Series,
    fast: int = _FAST_PERIOD,
    slow: int = _SLOW_PERIOD,
    signal: int = _SIGNAL_PERIOD,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Return (ppo, signal_line, histogram) series."""
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()

    ppo = ((ema_fast - ema_slow) / ema_slow * 100).fillna(0.0)
    sig = ppo.ewm(span=signal, adjust=False).mean().fillna(ppo)
    hist = (ppo - sig).fillna(0.0)

    return ppo, sig, hist


def _compute_ppo_score(
    ppo_val: float,
    sig_val: float,
    ppo_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Composite score 0–100."""
    above_pts = 35.0 if ppo_val > sig_val else 0.0
    pos_pts   = 35.0 if ppo_val > 0 else 0.0

    window = ppo_series.iloc[-lookback:].dropna()
    if len(window) < 10:
        pct_pts = 15.0
    else:
        pct_pts = float((window < ppo_val).mean()) * 30.0

    return round(above_pts + pos_pts + pct_pts, 1)


def _classify_signal(score: float | None) -> PPOSignal:
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
    signal: PPOSignal,
    ppo_val: float,
    ppo_above: bool,
    ppo_pos: bool,
    score: float,
) -> str:
    above_str = "高于信号线" if ppo_above else "低于信号线"
    pos_str   = "快线高于慢线（PPO>0）" if ppo_pos else "快线低于慢线（PPO<0）"
    labels: dict[PPOSignal, str] = {
        "strong_bull": (
            f"{ticker} PPO={ppo_val:.2f}%，{above_str}，{pos_str}（得分 {score:.0f}）：动量极强，趋势加速向上。"
        ),
        "bull": (
            f"{ticker} PPO={ppo_val:.2f}%，{above_str}，{pos_str}（得分 {score:.0f}）：动量偏强，多头趋势延续。"
        ),
        "neutral": (
            f"{ticker} PPO={ppo_val:.2f}%，{above_str}，{pos_str}（得分 {score:.0f}）：动量中性，趋势方向不明。"
        ),
        "bear": (
            f"{ticker} PPO={ppo_val:.2f}%，{above_str}，{pos_str}（得分 {score:.0f}）：动量偏弱，空头趋势延续。"
        ),
        "strong_bear": (
            f"{ticker} PPO={ppo_val:.2f}%，{above_str}，{pos_str}（得分 {score:.0f}）：动量极弱，趋势加速向下。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 PPO 指标。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_ppo(ticker: str) -> PPOData:
    """Compute Percentage Price Oscillator for *ticker*.

    Never raises. Returns PPOData with data_available=False on failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return PPOData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    if hist.empty or "Close" not in hist.columns:
        return PPOData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 PPO。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()

    if len(close) < _MIN_BARS:
        return PPOData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 PPO。",
            as_of_date=as_of,
        )

    ppo_s, sig_s, hist_s = _compute_ppo_series(close)

    ppo_val  = float(ppo_s.iloc[-1])
    sig_val  = float(sig_s.iloc[-1])
    hist_val = float(hist_s.iloc[-1])

    score  = _compute_ppo_score(ppo_val, sig_val, ppo_s)
    signal = _classify_signal(score)
    interp = _build_interpretation(
        ticker, signal, ppo_val, ppo_val > sig_val, ppo_val > 0, score
    )

    return PPOData(
        ticker=ticker,
        ppo_value=round(ppo_val, 4),
        signal_value=round(sig_val, 4),
        histogram=round(hist_val, 4),
        ppo_above_signal=ppo_val > sig_val,
        ppo_positive=ppo_val > 0,
        ppo_score=score,
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
