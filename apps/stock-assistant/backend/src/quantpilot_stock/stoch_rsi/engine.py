"""Stochastic RSI (StochRSI) — F.83.

Applies the Stochastic oscillator formula to RSI values instead of price,
creating a more sensitive momentum oscillator.

  RSI  = Wilder RSI(close, rsi_period)
  %K   = (RSI − min(RSI, stoch_period)) / (max(RSI, stoch_period) − min(RSI, stoch_period)) × 100
  %D   = SMA(%K, d_period)

  Defaults: rsi_period=14, stoch_period=14, k_period=3, d_period=3

Range: 0–100
  StochRSI %K > 80 → overbought
  StochRSI %K < 20 → oversold
  %K crosses above %D → bullish signal
  %K crosses below %D → bearish signal

Score (0–100):
  35 pts  %K > 50 (above midpoint)
  35 pts  %K > %D (bullish crossover position)
  30 pts  percentile rank of %K in rolling 252-bar window
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

StochRSISignal = Literal["strong_bull", "bull", "neutral", "bear", "strong_bear", "no_data"]

_MIN_BARS = 30  # need rsi_period + stoch_period + warm-up


@dataclass
class StochRSIData:
    ticker: str
    k_value: float | None    # %K (fast line)
    d_value: float | None    # %D (signal line = SMA of %K)
    stoch_rsi_score: float
    signal: StochRSISignal
    interpretation: str
    as_of_date: str
    data_available: bool


# ---------------------------------------------------------------------------
# Core math
# ---------------------------------------------------------------------------

def _compute_rsi(series: pd.Series, period: int) -> pd.Series:
    """Standard Wilder RSI."""
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.clip(lower=1e-10)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0).clip(0.0, 100.0)


def _compute_stoch_rsi_series(
    close: pd.Series,
    rsi_period: int = 14,
    stoch_period: int = 14,
    k_smooth: int = 3,
    d_period: int = 3,
) -> tuple[pd.Series, pd.Series]:
    """Return (%K, %D) series, both in range 0–100."""
    rsi = _compute_rsi(close, rsi_period)

    rsi_low = rsi.rolling(stoch_period).min()
    rsi_high = rsi.rolling(stoch_period).max()

    hl_range = (rsi_high - rsi_low).replace(0.0, float("nan"))
    raw_k = ((rsi - rsi_low) / hl_range * 100.0).fillna(50.0).clip(0.0, 100.0)

    # Smooth %K
    k = raw_k.rolling(k_smooth).mean().fillna(raw_k)
    d = k.rolling(d_period).mean().fillna(k)

    return k.clip(0.0, 100.0), d.clip(0.0, 100.0)


def _compute_stoch_rsi_score(k_series: pd.Series, d_series: pd.Series) -> float:
    """Composite 0–100 score."""
    score = 0.0
    k_last = float(k_series.iloc[-1])
    d_last = float(d_series.iloc[-1])

    # 35 pts: %K > 50
    if k_last > 50.0:
        score += 35.0

    # 35 pts: %K > %D (bullish position)
    if k_last > d_last:
        score += 35.0

    # 30 pts: percentile rank of %K in 252-bar window
    window = min(252, len(k_series))
    if window >= 10:
        k_win = k_series.iloc[-window:]
        pct = float((k_win < k_last).sum()) / max(1, len(k_win))
        score += pct * 30.0

    return round(min(100.0, max(0.0, score)), 2)


def _classify_signal(score: float | None) -> StochRSISignal:
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
    score: float,
    signal: StochRSISignal,
    k: float,
    d: float,
) -> str:
    parts: list[str] = []
    sig_map = {
        "strong_bull": "极佳",
        "bull": "偏强",
        "neutral": "中性",
        "bear": "偏弱",
        "strong_bear": "极弱",
        "no_data": "数据不足",
    }
    parts.append(f"Stochastic RSI 综合评分 {score:.1f}/100，信号{sig_map.get(signal, signal)}。")
    parts.append(f"%K={k:.1f}，%D={d:.1f}。")
    if k > 80:
        parts.append("StochRSI 超买区间（%K>80），注意动量过热风险。")
    elif k < 20:
        parts.append("StochRSI 超卖区间（%K<20），可能存在反弹机会。")
    else:
        parts.append("StochRSI 处于中性区间（20~80）。")
    if k > d:
        parts.append("%K 在 %D 上方，短期动量偏多。")
    else:
        parts.append("%K 在 %D 下方，短期动量偏空。")
    parts.append("StochRSI 比标准 RSI 更敏感，适合短线捕捉超买超卖极值。")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def compute_stoch_rsi(ticker: str) -> StochRSIData:
    """Fetch OHLCV from yfinance and compute Stochastic RSI."""
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period="2y")
        if df.empty or len(df) < _MIN_BARS:
            return StochRSIData(
                ticker=ticker,
                k_value=None,
                d_value=None,
                stoch_rsi_score=0.0,
                signal="no_data",
                interpretation="数据不足，无法计算 Stochastic RSI。",
                as_of_date=str(date.today()),
                data_available=True,
            )

        close = df["Close"].dropna()
        k_series, d_series = _compute_stoch_rsi_series(close)

        k_last = float(k_series.iloc[-1])
        d_last = float(d_series.iloc[-1])

        score = _compute_stoch_rsi_score(k_series, d_series)
        sig = _classify_signal(score)
        interp = _build_interpretation(score, sig, k_last, d_last)

        as_of = str(df.index[-1].date()) if hasattr(df.index[-1], "date") else str(date.today())

        return StochRSIData(
            ticker=ticker,
            k_value=round(k_last, 2),
            d_value=round(d_last, 2),
            stoch_rsi_score=score,
            signal=sig,
            interpretation=interp,
            as_of_date=as_of,
            data_available=True,
        )

    except Exception:
        return StochRSIData(
            ticker=ticker,
            k_value=None,
            d_value=None,
            stoch_rsi_score=0.0,
            signal="no_data",
            interpretation="数据获取失败。",
            as_of_date=str(date.today()),
            data_available=False,
        )
