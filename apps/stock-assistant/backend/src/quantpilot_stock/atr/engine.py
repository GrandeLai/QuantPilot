"""Average True Range (ATR) engine — Phase F.46.

ATR = Wilder EWM(alpha=1/14, adjust=False) of True Range.
True Range = max(High-Low, |High-PrevClose|, |Low-PrevClose|).
ATR% = ATR / Close × 100  (normalised volatility).

Score combines trend direction (price vs SMA20/SMA50) with ATR confirmation:

  raw =
    +2  / -2 : price above / below SMA20
    +1  / -1 : price above / below SMA50
    +0.5/-0.5: ATR% in top-25th percentile amplifies trend direction
    +0.25    : ATR% in bottom-25th percentile (compression → coiled spring, mildly bullish)

  raw ∈ [-3.5, 3.5] nominal → map via (raw + 3.5) / 7 × 100.

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

ATRSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]

_ATR_PERIOD = 14
_MIN_BARS = 60   # Need SMA50 + ATR warmup


@dataclass
class ATRData:
    ticker: str
    atr: float | None = None             # Latest ATR (price units)
    atr_pct: float | None = None         # ATR / Close × 100
    atr_pct_rank: float | None = None    # Percentile rank in 1-year window [0,1]
    volatility_regime: str = ""          # "high" | "normal" | "low" (compression)
    above_sma20: bool = False
    above_sma50: bool = False
    atr_score: float = 50.0             # 0-100
    signal: ATRSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_atr_series(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = _ATR_PERIOD,
) -> pd.Series:
    """Return ATR series using Wilder smoothing."""
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)

    # Wilder EWM: alpha = 1/period
    atr = tr.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    return atr


def _compute_atr_score(
    above_sma20: bool,
    above_sma50: bool,
    atr_pct_rank: float | None,
) -> float:
    """Composite ATR score in [0, 100].

    Raw range [-3.5, 3.5]:
      ±2   : SMA20 direction (primary trend)
      ±1   : SMA50 direction (secondary trend)
      ±0.5 : ATR top-quartile amplifies trend (confirmed breakout/breakdown)
      +0.25: ATR bottom-quartile compression bias (coiled spring)
    """
    raw = 2.0 if above_sma20 else -2.0
    raw += 1.0 if above_sma50 else -1.0

    if atr_pct_rank is not None:
        if atr_pct_rank >= 0.75:
            raw += 0.5 if (above_sma20 and above_sma50) else -0.5
        elif atr_pct_rank <= 0.25:
            raw += 0.25   # compression → mild positive bias

    return float(max(0.0, min(100.0, (raw + 3.5) / 7.0 * 100.0)))


def _classify_signal(atr_score: float | None) -> ATRSignal:
    if atr_score is None:
        return "no_data"
    if atr_score >= 80:
        return "strong_bull"
    if atr_score >= 60:
        return "bull"
    if atr_score >= 40:
        return "neutral"
    if atr_score >= 20:
        return "bear"
    return "strong_bear"


def _build_interpretation(
    ticker: str,
    signal: ATRSignal,
    atr: float,
    atr_pct: float,
    volatility_regime: str,
    above_sma20: bool,
    above_sma50: bool,
) -> str:
    regime_text = {
        "high": "高波动（趋势扩张期）",
        "normal": "正常波动",
        "low": "低波动（盘整压缩期）",
    }.get(volatility_regime, "")

    labels: dict[ATRSignal, str] = {
        "strong_bull": f"{ticker} ATR {atr:.2f}（{atr_pct:.1f}%），{regime_text}：多头趋势强劲，均线上方运行。",
        "bull": f"{ticker} ATR {atr:.2f}（{atr_pct:.1f}%），{regime_text}：多头趋势为主，均线偏多排列。",
        "neutral": f"{ticker} ATR {atr:.2f}（{atr_pct:.1f}%），{regime_text}：趋势不明，均线交织。",
        "bear": f"{ticker} ATR {atr:.2f}（{atr_pct:.1f}%），{regime_text}：空头趋势为主，均线偏空排列。",
        "strong_bear": f"{ticker} ATR {atr:.2f}（{atr_pct:.1f}%），{regime_text}：空头趋势强劲，均线下方运行。",
        "no_data": f"{ticker} 数据不足，无法计算 ATR。",
    }
    parts = [labels.get(signal, "")]
    if volatility_regime == "low":
        parts.append("（波动率压缩，关注突破方向）")
    elif volatility_regime == "high":
        pos = "上行" if (above_sma20 and above_sma50) else "下行"
        parts.append(f"（波动率扩张，趋势{pos}确认）")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_atr(ticker: str) -> ATRData:
    """Compute ATR data for *ticker*.

    Never raises. Returns ATRData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="2y", interval="1d")  # 2y for percentile rank
    except Exception:
        return ATRData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    required = {"High", "Low", "Close"}
    if hist.empty or not required.issubset(hist.columns):
        return ATRData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 ATR。",
            as_of_date=as_of,
        )

    high = hist["High"].dropna()
    low = hist["Low"].dropna()
    close = hist["Close"].dropna()

    common_idx = high.index.intersection(low.index).intersection(close.index)
    high = high.loc[common_idx]
    low = low.loc[common_idx]
    close = close.loc[common_idx]

    if len(close) < _MIN_BARS:
        return ATRData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 ATR。",
            as_of_date=as_of,
        )

    atr_series = _compute_atr_series(high, low, close)
    atr_val = float(atr_series.iloc[-1])
    close_val = float(close.iloc[-1])

    atr_pct = (atr_val / close_val * 100.0) if close_val > 0 else None

    # ATR% percentile over last 252 bars (≈1 year)
    lookback = min(252, len(atr_series))
    atr_pct_series = (atr_series / close * 100.0).iloc[-lookback:]
    atr_pct_val = float(atr_pct_series.iloc[-1]) if atr_pct is not None else None
    valid_pct = atr_pct_series.dropna()
    if len(valid_pct) >= 20 and atr_pct_val is not None:
        rank = float((valid_pct < atr_pct_val).mean())
    else:
        rank = None

    # Volatility regime
    if rank is not None:
        if rank >= 0.75:
            regime = "high"
        elif rank <= 0.25:
            regime = "low"
        else:
            regime = "normal"
    else:
        regime = "normal"

    sma20 = float(close.iloc[-20:].mean()) if len(close) >= 20 else None
    sma50 = float(close.iloc[-50:].mean()) if len(close) >= 50 else None

    above_sma20 = (close_val > sma20) if sma20 is not None else False
    above_sma50 = (close_val > sma50) if sma50 is not None else False

    atr_score = _compute_atr_score(above_sma20, above_sma50, rank)
    signal = _classify_signal(atr_score)
    interpretation = _build_interpretation(
        ticker, signal, atr_val,
        atr_pct if atr_pct is not None else 0.0,
        regime, above_sma20, above_sma50
    )

    return ATRData(
        ticker=ticker,
        atr=round(atr_val, 4),
        atr_pct=round(atr_pct, 2) if atr_pct is not None else None,
        atr_pct_rank=round(rank, 3) if rank is not None else None,
        volatility_regime=regime,
        above_sma20=above_sma20,
        above_sma50=above_sma50,
        atr_score=round(atr_score, 1),
        signal=signal,
        interpretation=interpretation,
        as_of_date=as_of,
        data_available=True,
    )
