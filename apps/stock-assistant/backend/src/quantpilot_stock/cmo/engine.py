"""Chande Momentum Oscillator (CMO) engine — Phase F.65.

  Up[i]   = max(Close[i] − Close[i-1], 0)
  Down[i] = max(Close[i-1] − Close[i], 0)
  CMO(n)  = 100 × (ΣUp − ΣDown) / (ΣUp + ΣDown)   over n bars (default 14)
  Signal  = SMA(9, CMO)

Score (0–100):
  35 pts  CMO > Signal (momentum above smoothed line)
  35 pts  CMO > 0     (net positive momentum)
  30 pts  percentile rank of CMO in 252-bar window × 30

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

CMOSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_CMO_PERIOD    = 14
_SIGNAL_PERIOD = 9
_MIN_BARS      = _CMO_PERIOD + _SIGNAL_PERIOD + 5


@dataclass
class CMOData:
    ticker: str
    cmo_value: float | None = None          # −100 … +100
    signal_value: float | None = None       # SMA(9, CMO)
    cmo_above_signal: bool | None = None    # CMO > Signal
    cmo_positive: bool | None = None        # CMO > 0
    cmo_score: float = 50.0                 # 0–100 composite
    signal: CMOSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_cmo_series(
    close: pd.Series,
    cmo_period: int = _CMO_PERIOD,
    signal_period: int = _SIGNAL_PERIOD,
) -> tuple[pd.Series, pd.Series]:
    """Return (cmo, signal) series."""
    diff = close.diff()
    up   = diff.clip(lower=0.0)
    down = (-diff).clip(lower=0.0)

    sum_up   = up.rolling(cmo_period).sum()
    sum_down = down.rolling(cmo_period).sum()
    total    = sum_up + sum_down

    # Avoid division by zero when there's no price change
    cmo = pd.Series(
        (100.0 * (sum_up - sum_down) / total).where(total > 0, 0.0),
        index=close.index,
    ).ffill().fillna(0.0)

    signal = cmo.rolling(signal_period).mean().ffill().fillna(cmo)
    return cmo, signal


def _compute_cmo_score(
    cmo_val: float,
    sig_val: float,
    cmo_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Composite score 0–100."""
    above_pts = 35.0 if cmo_val > sig_val else 0.0
    pos_pts   = 35.0 if cmo_val > 0 else 0.0

    window = cmo_series.iloc[-lookback:].dropna()
    if len(window) < 10:
        pct_pts = 15.0
    else:
        pct_pts = float((window < cmo_val).mean()) * 30.0

    return round(above_pts + pos_pts + pct_pts, 1)


def _classify_signal(score: float | None) -> CMOSignal:
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
    signal: CMOSignal,
    cmo_val: float,
    cmo_above: bool,
    cmo_pos: bool,
    score: float,
) -> str:
    above_str = "高于信号线" if cmo_above else "低于信号线"
    pos_str   = "净买入（CMO>0）" if cmo_pos else "净卖出（CMO<0）"
    labels: dict[CMOSignal, str] = {
        "strong_bull": (
            f"{ticker} CMO={cmo_val:.1f}，{above_str}，{pos_str}（得分 {score:.0f}）：动量极强，多头动能显著。"
        ),
        "bull": (
            f"{ticker} CMO={cmo_val:.1f}，{above_str}，{pos_str}（得分 {score:.0f}）：动量偏强，多头占优。"
        ),
        "neutral": (
            f"{ticker} CMO={cmo_val:.1f}，{above_str}，{pos_str}（得分 {score:.0f}）：动量中性，观望为主。"
        ),
        "bear": (
            f"{ticker} CMO={cmo_val:.1f}，{above_str}，{pos_str}（得分 {score:.0f}）：动量偏弱，空头占优。"
        ),
        "strong_bear": (
            f"{ticker} CMO={cmo_val:.1f}，{above_str}，{pos_str}（得分 {score:.0f}）：动量极弱，空头动能显著。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 CMO 指标。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_cmo(ticker: str) -> CMOData:
    """Compute Chande Momentum Oscillator for *ticker*.

    Never raises. Returns CMOData with data_available=False on failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return CMOData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    if hist.empty or "Close" not in hist.columns:
        return CMOData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 CMO。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()

    if len(close) < _MIN_BARS:
        return CMOData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 CMO。",
            as_of_date=as_of,
        )

    cmo_s, sig_s = _compute_cmo_series(close)

    cmo_val = float(cmo_s.iloc[-1])
    sig_val = float(sig_s.iloc[-1])

    score  = _compute_cmo_score(cmo_val, sig_val, cmo_s)
    signal = _classify_signal(score)
    interp = _build_interpretation(
        ticker, signal, cmo_val, cmo_val > sig_val, cmo_val > 0, score
    )

    return CMOData(
        ticker=ticker,
        cmo_value=round(cmo_val, 2),
        signal_value=round(sig_val, 2),
        cmo_above_signal=cmo_val > sig_val,
        cmo_positive=cmo_val > 0,
        cmo_score=score,
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
