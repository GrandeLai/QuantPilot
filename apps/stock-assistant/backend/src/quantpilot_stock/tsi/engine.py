"""TSI (True Strength Index) engine — Phase F.57.

PC       = Close − Close[−1]
TSI      = 100 × EMA(EMA(PC, 25), 13) / EMA(EMA(|PC|, 25), 13)
Signal   = EMA(TSI, 7)

Score = percentile rank of TSI in last 252 bars × 100.

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

TSISignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_FAST_PERIOD    = 25
_SLOW_PERIOD    = 13
_SIGNAL_PERIOD  = 7
_OVERBOUGHT     = 25.0
_OVERSOLD       = -25.0
_MIN_BARS       = _FAST_PERIOD + _SLOW_PERIOD + 10


@dataclass
class TSIData:
    ticker: str
    tsi_value: float | None = None         # −100 to +100
    signal_line: float | None = None       # 7-period EMA of TSI
    tsi_positive: bool = False             # TSI > 0
    tsi_above_signal: bool = False         # TSI > signal line
    tsi_score: float = 50.0              # 0–100 percentile
    signal: TSISignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_tsi_series(
    close: pd.Series,
    fast: int = _FAST_PERIOD,
    slow: int = _SLOW_PERIOD,
    signal: int = _SIGNAL_PERIOD,
) -> tuple[pd.Series, pd.Series]:
    """Return (tsi_series, signal_series).

    Both series have the same length as *close*.
    NaN values at the start are replaced with 0.0.
    """
    pc     = close.diff()
    abs_pc = pc.abs()

    ema_pc1 = pc.ewm(span=fast, adjust=False).mean()
    ema_pc2 = ema_pc1.ewm(span=slow, adjust=False).mean()

    ema_abs1 = abs_pc.ewm(span=fast, adjust=False).mean()
    ema_abs2 = ema_abs1.ewm(span=slow, adjust=False).mean()

    tsi_raw = 100.0 * ema_pc2 / ema_abs2.replace(0.0, float("nan"))
    tsi     = tsi_raw.fillna(0.0)

    sig = tsi.ewm(span=signal, adjust=False).mean()
    return tsi, sig


def _compute_tsi_score(
    tsi_val: float,
    tsi_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Percentile rank of tsi_val in last *lookback* bars × 100."""
    window = tsi_series.iloc[-lookback:].dropna()
    if len(window) < 10:
        # fallback: map [−100, +100] → [0, 100]
        return float(max(0.0, min(100.0, (tsi_val + 100.0) / 200.0 * 100.0)))
    rank = float((window < tsi_val).mean())
    return round(rank * 100.0, 1)


def _classify_signal(score: float | None) -> TSISignal:
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
    signal: TSISignal,
    tsi: float,
    sig_line: float,
    score: float,
    positive: bool,
    above_signal: bool,
) -> str:
    cross = "高于信号线（看涨）" if above_signal else "低于信号线（看跌）"
    extreme = ""
    if tsi > _OVERBOUGHT:
        extreme = "（超买区间）"
    elif tsi < _OVERSOLD:
        extreme = "（超卖区间）"

    labels: dict[TSISignal, str] = {
        "strong_bull": (
            f"{ticker} TSI {tsi:+.2f}{extreme}，{cross}（百分位 {score:.0f}）："
            f"双重平滑动量极强。"
        ),
        "bull": (
            f"{ticker} TSI {tsi:+.2f}{extreme}，{cross}（百分位 {score:.0f}）："
            f"动量偏正，看涨信号。"
        ),
        "neutral": (
            f"{ticker} TSI {tsi:+.2f}{extreme}，{cross}（百分位 {score:.0f}）："
            f"动量中性，无明显方向。"
        ),
        "bear": (
            f"{ticker} TSI {tsi:+.2f}{extreme}，{cross}（百分位 {score:.0f}）："
            f"动量偏负，看跌信号。"
        ),
        "strong_bear": (
            f"{ticker} TSI {tsi:+.2f}{extreme}，{cross}（百分位 {score:.0f}）："
            f"双重平滑动量极弱。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 TSI。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_tsi(ticker: str) -> TSIData:
    """Compute TSI for *ticker*.

    Never raises. Returns TSIData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return TSIData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    if hist.empty or "Close" not in hist.columns:
        return TSIData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 TSI。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()

    if len(close) < _MIN_BARS:
        return TSIData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 TSI。",
            as_of_date=as_of,
        )

    tsi_series, sig_series = _compute_tsi_series(close)

    tsi_val  = float(tsi_series.iloc[-1])
    sig_val  = float(sig_series.iloc[-1])
    positive = tsi_val > 0.0
    above    = tsi_val > sig_val

    score  = _compute_tsi_score(tsi_val, tsi_series)
    signal = _classify_signal(score)
    interp = _build_interpretation(ticker, signal, tsi_val, sig_val, score, positive, above)

    return TSIData(
        ticker=ticker,
        tsi_value=round(tsi_val, 4),
        signal_line=round(sig_val, 4),
        tsi_positive=positive,
        tsi_above_signal=above,
        tsi_score=round(score, 1),
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
