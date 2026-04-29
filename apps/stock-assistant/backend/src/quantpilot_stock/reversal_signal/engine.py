"""Short-Term Reversal Signal engine — Phase F.34.

Based on Jegadeesh (1990) short-term reversal: stocks that have
underperformed vs SPY over the past 1-4 weeks tend to outperform in the
following month. Contrarian to long-term momentum (F.33 RS Score).

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd
import yfinance as yf

ReversalSignal = Literal[
    "strong_reversal_up",
    "reversal_up",
    "neutral",
    "reversal_down",
    "strong_reversal_down",
    "no_data",
]


@dataclass
class ReversalData:
    ticker: str
    ret_1w: float | None = None       # 1-week total return (decimal)
    ret_4w: float | None = None       # 4-week total return (decimal)
    rel_1w: float | None = None       # 1-week return relative to SPY
    rel_4w: float | None = None       # 4-week return relative to SPY
    vol_ratio: float | None = None    # 5-day avg vol / 20-day avg vol
    reversal_score: float = 0.0       # -100 to +100
    signal: ReversalSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _period_return(close: pd.Series, n_bars: int) -> float | None:
    """Total return over last *n_bars* bars of *close*."""
    if len(close) < n_bars + 1:
        return None
    start = float(close.iloc[-(n_bars + 1)])
    end = float(close.iloc[-1])
    if start <= 0:
        return None
    return (end - start) / start


def _compute_reversal_score(
    rel_1w: float,
    rel_4w: float,
    vol_ratio: float | None,
) -> float:
    """Compute reversal score in [-100, 100].

    Positive = contrarian long setup (stock underperformed → expect bounce).
    Negative = contrarian short setup (stock outperformed → expect fade).
    """
    score = 0.0

    # 1-week relative performance component (max ±40)
    if rel_1w < -0.05:
        score += 40.0
    elif rel_1w < -0.02:
        score += 25.0
    elif rel_1w < -0.01:
        # Linear interpolation between -1% and -2%
        score += 25.0 * (abs(rel_1w) - 0.01) / 0.01
    elif rel_1w > 0.05:
        score -= 40.0
    elif rel_1w > 0.02:
        score -= 25.0
    elif rel_1w > 0.01:
        score -= 25.0 * (rel_1w - 0.01) / 0.01

    # 4-week relative performance component (max ±40)
    if rel_4w < -0.10:
        score += 40.0
    elif rel_4w < -0.05:
        score += 25.0
    elif rel_4w < -0.02:
        score += 25.0 * (abs(rel_4w) - 0.02) / 0.03
    elif rel_4w > 0.10:
        score -= 40.0
    elif rel_4w > 0.05:
        score -= 25.0
    elif rel_4w > 0.02:
        score -= 25.0 * (rel_4w - 0.02) / 0.03

    # Volume confirmation component (max ±20)
    # Low volume on weakness → more likely bounce; high volume → trend continuation
    if vol_ratio is not None:
        if vol_ratio < 0.7 and rel_1w < 0:
            # Quiet selling → potential reversal up
            score += 20.0
        elif vol_ratio < 0.7 and rel_1w > 0:
            # Quiet buying → potential reversal down
            score -= 20.0

    return float(max(-100.0, min(100.0, score)))


def _classify_signal(reversal_score: float | None) -> ReversalSignal:
    """Map reversal score to signal."""
    if reversal_score is None:
        return "no_data"
    if reversal_score >= 60:
        return "strong_reversal_up"
    if reversal_score >= 30:
        return "reversal_up"
    if reversal_score > -30:
        return "neutral"
    if reversal_score > -60:
        return "reversal_down"
    return "strong_reversal_down"


def _build_interpretation(
    ticker: str,
    signal: ReversalSignal,
    rel_1w: float | None,
    rel_4w: float | None,
    reversal_score: float,
    vol_ratio: float | None,
) -> str:
    labels: dict[ReversalSignal, str] = {
        "strong_reversal_up": (
            f"{ticker} 短期反转评分 {reversal_score:.0f}：强多头反转信号——近期显著跑输大盘，"
            "统计上次月有超额回报机会，可关注企稳信号入场。"
        ),
        "reversal_up": (
            f"{ticker} 短期反转评分 {reversal_score:.0f}：轻度多头反转倾向，"
            "近期跑输大盘，但需结合基本面与催化剂确认。"
        ),
        "neutral": (
            f"{ticker} 短期反转评分 {reversal_score:.0f}：无明显短期反转信号，"
            "与大盘表现接近，维持观望。"
        ),
        "reversal_down": (
            f"{ticker} 短期反转评分 {reversal_score:.0f}：轻度空头反转倾向，"
            "近期跑赢大盘，短期可能回归均值，注意止盈。"
        ),
        "strong_reversal_down": (
            f"{ticker} 短期反转评分 {reversal_score:.0f}：强空头反转信号——近期显著跑赢大盘，"
            "统计上次月有均值回归风险，可考虑减仓或止盈。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算短期反转信号。",
    }
    parts = [labels.get(signal, "")]
    details = []
    if rel_1w is not None:
        details.append(f"1W 超额 {rel_1w * 100:+.1f}%")
    if rel_4w is not None:
        details.append(f"4W 超额 {rel_4w * 100:+.1f}%")
    if vol_ratio is not None:
        details.append(f"量比 {vol_ratio:.2f}×")
    if details:
        parts.append("（" + " | ".join(details) + "）")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_reversal(ticker: str) -> ReversalData:
    """Compute short-term reversal signal for *ticker* vs SPY.

    Never raises. Returns ReversalData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk_stock = yf.Ticker(ticker)
        tk_spy = yf.Ticker("SPY")
        hist_stock = tk_stock.history(period="2y", interval="1d")
        hist_spy = tk_spy.history(period="2y", interval="1d")
    except Exception:
        return ReversalData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    if (
        hist_stock.empty
        or hist_spy.empty
        or "Close" not in hist_stock.columns
        or "Close" not in hist_spy.columns
    ):
        return ReversalData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史价格数据为空，无法计算反转信号。",
            as_of_date=as_of,
        )

    close_stock = hist_stock["Close"].dropna()
    close_spy = hist_spy["Close"].dropna()
    volume_stock = hist_stock["Volume"].dropna() if "Volume" in hist_stock.columns else pd.Series(dtype=float)

    if len(close_stock) < 25 or len(close_spy) < 25:
        return ReversalData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 25 个交易日，无法计算反转信号。",
            as_of_date=as_of,
        )

    # Period returns
    ret_1w_stock = _period_return(close_stock, 5)
    ret_4w_stock = _period_return(close_stock, 20)
    ret_1w_spy = _period_return(close_spy, 5)
    ret_4w_spy = _period_return(close_spy, 20)

    if any(v is None for v in [ret_1w_stock, ret_4w_stock, ret_1w_spy, ret_4w_spy]):
        return ReversalData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 有效数据不足，无法计算相对表现。",
            as_of_date=as_of,
        )

    # All four are guaranteed non-None by the guard above
    rel_1w = float(ret_1w_stock or 0) - float(ret_1w_spy or 0)
    rel_4w = float(ret_4w_stock or 0) - float(ret_4w_spy or 0)

    # Volume ratio
    vol_ratio: float | None = None
    if len(volume_stock) >= 20:
        vol5 = float(volume_stock.iloc[-5:].mean()) if len(volume_stock) >= 5 else None
        vol20 = float(volume_stock.iloc[-20:].mean())
        if vol5 is not None and vol20 > 0:
            vol_ratio = vol5 / vol20

    reversal_score = _compute_reversal_score(rel_1w, rel_4w, vol_ratio)
    signal = _classify_signal(reversal_score)
    interpretation = _build_interpretation(
        ticker, signal, rel_1w, rel_4w, reversal_score, vol_ratio
    )

    return ReversalData(
        ticker=ticker,
        ret_1w=ret_1w_stock,
        ret_4w=ret_4w_stock,
        rel_1w=rel_1w,
        rel_4w=rel_4w,
        vol_ratio=vol_ratio,
        reversal_score=round(reversal_score, 1),
        signal=signal,
        interpretation=interpretation,
        as_of_date=as_of,
        data_available=True,
    )
