"""Vortex Indicator engine — Phase F.63.

Identifies trending markets and their direction:

  TR       = max(|High−Low|, |High−PrevClose|, |Low−PrevClose|)
  VM+      = |High[i] − Low[i-1]|   (up-trend vortex movement)
  VM-      = |Low[i]  − High[i-1]|  (down-trend vortex movement)
  +VI(14)  = sum(VM+, 14) / sum(TR, 14)
  -VI(14)  = sum(VM-, 14) / sum(TR, 14)

  Spread   = +VI − -VI

Score (0–100) = percentile rank of Spread in last 252 bars × 100.

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

VortexSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_PERIOD   = 14
_MIN_BARS = _PERIOD + 5


@dataclass
class VortexData:
    ticker: str
    vi_plus: float | None = None           # +VI (14)
    vi_minus: float | None = None          # -VI (14)
    vi_spread: float | None = None         # +VI - -VI
    vi_bullish: bool | None = None         # +VI > -VI
    vortex_score: float = 50.0            # 0–100 percentile
    signal: VortexSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_vortex_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = _PERIOD,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Return (+VI, -VI, spread) series."""
    prev_close = close.shift(1)
    prev_high  = high.shift(1)
    prev_low   = low.shift(1)

    tr = pd.concat([
        (high - low).abs(),
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)

    vm_plus  = (high - prev_low).abs()
    vm_minus = (low  - prev_high).abs()

    vi_plus  = vm_plus.rolling(period).sum()  / tr.rolling(period).sum()
    vi_minus = vm_minus.rolling(period).sum() / tr.rolling(period).sum()

    vi_plus  = vi_plus.ffill().fillna(1.0)
    vi_minus = vi_minus.ffill().fillna(1.0)
    spread   = vi_plus - vi_minus
    return vi_plus, vi_minus, spread


def _compute_vortex_score(
    spread_val: float,
    spread_series: pd.Series,
    lookback: int = 252,
) -> float:
    """Percentile rank of spread in last *lookback* bars × 100."""
    window = spread_series.iloc[-lookback:].dropna()
    if len(window) < 10:
        return 50.0
    rank = float((window < spread_val).mean())
    return round(rank * 100.0, 1)


def _classify_signal(score: float | None) -> VortexSignal:
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
    signal: VortexSignal,
    vi_plus: float,
    vi_minus: float,
    score: float,
) -> str:
    dir_str = "+VI > -VI（上涨趋势）" if vi_plus > vi_minus else "-VI > +VI（下跌趋势）"
    labels: dict[VortexSignal, str] = {
        "strong_bull": (
            f"{ticker} +VI={vi_plus:.3f}，-VI={vi_minus:.3f}，{dir_str}（百分位 {score:.0f}）：上涨涡旋极强。"
        ),
        "bull": (
            f"{ticker} +VI={vi_plus:.3f}，-VI={vi_minus:.3f}，{dir_str}（百分位 {score:.0f}）：上涨动量偏强。"
        ),
        "neutral": (
            f"{ticker} +VI={vi_plus:.3f}，-VI={vi_minus:.3f}，{dir_str}（百分位 {score:.0f}）：涡旋方向中性。"
        ),
        "bear": (
            f"{ticker} +VI={vi_plus:.3f}，-VI={vi_minus:.3f}，{dir_str}（百分位 {score:.0f}）：下跌动量偏强。"
        ),
        "strong_bear": (
            f"{ticker} +VI={vi_plus:.3f}，-VI={vi_minus:.3f}，{dir_str}（百分位 {score:.0f}）：下跌涡旋极强。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算涡旋指标。",
    }
    return labels.get(signal, "")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_vortex(ticker: str) -> VortexData:
    """Compute Vortex Indicator for *ticker*.

    Never raises. Returns VortexData with data_available=False on failure.
    """
    as_of = date.today().isoformat()

    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")
    except Exception:
        return VortexData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    required = {"High", "Low", "Close"}
    if hist.empty or not required.issubset(hist.columns):
        return VortexData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算涡旋指标。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()
    high  = hist["High"].loc[close.index].dropna()
    low   = hist["Low"].loc[close.index].dropna()

    common = close.index.intersection(high.index).intersection(low.index)
    close, high, low = close.loc[common], high.loc[common], low.loc[common]

    if len(close) < _MIN_BARS:
        return VortexData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算涡旋指标。",
            as_of_date=as_of,
        )

    vip_s, vim_s, spread_s = _compute_vortex_series(high, low, close)

    vip_val    = float(vip_s.iloc[-1])
    vim_val    = float(vim_s.iloc[-1])
    spread_val = float(spread_s.iloc[-1])

    score  = _compute_vortex_score(spread_val, spread_s)
    signal = _classify_signal(score)
    interp = _build_interpretation(ticker, signal, vip_val, vim_val, score)

    return VortexData(
        ticker=ticker,
        vi_plus=round(vip_val, 4),
        vi_minus=round(vim_val, 4),
        vi_spread=round(spread_val, 4),
        vi_bullish=vip_val > vim_val,
        vortex_score=score,
        signal=signal,
        interpretation=interp,
        as_of_date=as_of,
        data_available=True,
    )
