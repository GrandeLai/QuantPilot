"""MACD Signal engine — Phase F.37.

Computes MACD (EMA12−EMA26), signal line (EMA9 of MACD), histogram,
recent crossover detection, and composite bull/bear score (0-100).

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import yfinance as yf

MACDSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]


@dataclass
class MACDData:
    ticker: str
    macd: float | None = None           # MACD line (EMA12 − EMA26)
    signal_line: float | None = None    # Signal line (EMA9 of MACD)
    histogram: float | None = None      # MACD − Signal
    prev_histogram: float | None = None # Previous bar's histogram
    histogram_expanding: bool = False   # |hist[-1]| > |hist[-2]|
    recent_crossover: bool = False      # Crossover in last 3 bars
    crossover_direction: str = ""       # "bull" | "bear" | ""
    macd_score: float = 50.0            # 0-100
    signal: MACDSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_MIN_BARS = 35   # 26 (slow EMA) + 9 (signal EMA) − 1 + 1 guard


def _compute_macd_series(
    close: "pd.Series",  # type: ignore[name-defined]  # noqa: F821
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
) -> tuple["pd.Series", "pd.Series", "pd.Series"]:  # type: ignore[name-defined]  # noqa: F821
    """Return (macd_line, signal_line, histogram) as Series."""
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    sig_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    hist = macd_line - sig_line
    return macd_line, sig_line, hist


def _compute_macd_score(
    macd: float | None,
    signal_line: float | None,
    histogram: float | None,
    prev_histogram: float | None,
    recent_crossover: bool,
    crossover_direction: str,
) -> float:
    """Composite MACD score mapped to [0, 100].

    Raw range [-6, 6]:
      ±2: MACD sign (>0 → +2; <0 → -2)
      ±2: MACD vs signal (macd>sig → +2; macd<sig → -2)
      ±1: histogram expanding in its current direction
      ±1: recent crossover (bull cross +1; bear cross -1)

    Map: (raw + 6) / 12 * 100 → [0, 100].
    """
    raw = 0.0

    if macd is not None:
        raw += 2.0 if macd > 0 else -2.0

    if histogram is not None:
        raw += 2.0 if histogram > 0 else -2.0

    if histogram is not None and prev_histogram is not None:
        expanding = abs(histogram) > abs(prev_histogram)
        if expanding:
            raw += 1.0 if histogram > 0 else -1.0

    if recent_crossover:
        raw += 1.0 if crossover_direction == "bull" else -1.0

    # Map [-6, 6] → [0, 100]
    normalized = (raw + 6.0) / 12.0 * 100.0
    return float(max(0.0, min(100.0, normalized)))


def _classify_signal(macd_score: float | None) -> MACDSignal:
    if macd_score is None:
        return "no_data"
    if macd_score >= 80:
        return "strong_bull"
    if macd_score >= 60:
        return "bull"
    if macd_score >= 40:
        return "neutral"
    if macd_score >= 20:
        return "bear"
    return "strong_bear"


def _build_interpretation(
    ticker: str,
    signal: MACDSignal,
    macd_score: float,
    macd: float | None,
    histogram: float | None,
    recent_crossover: bool,
    crossover_direction: str,
) -> str:
    labels: dict[MACDSignal, str] = {
        "strong_bull": (
            f"{ticker} MACD评分 {macd_score:.0f}：强势多头信号，MACD在零线上方且柱状图扩张，动能强劲。"
        ),
        "bull": (
            f"{ticker} MACD评分 {macd_score:.0f}：偏多头，MACD处于有利位置，趋势向上。"
        ),
        "neutral": (
            f"{ticker} MACD评分 {macd_score:.0f}：中性，MACD多空力量均衡，等待方向确认。"
        ),
        "bear": (
            f"{ticker} MACD评分 {macd_score:.0f}：偏空头，MACD处于不利位置，趋势向下。"
        ),
        "strong_bear": (
            f"{ticker} MACD评分 {macd_score:.0f}：强势空头信号，MACD在零线下方且柱状图扩张，下跌动能强劲。"
        ),
        "no_data": f"{ticker} 数据不足，无法计算 MACD。",
    }
    parts = [labels.get(signal, "")]
    if recent_crossover:
        direction = "金叉（看涨）" if crossover_direction == "bull" else "死叉（看跌）"
        parts.append(f"（近期 MACD {direction}）")
    elif histogram is not None:
        if histogram > 0:
            parts.append("（柱状图为正，MACD 在 Signal 上方）")
        else:
            parts.append("（柱状图为负，MACD 在 Signal 下方）")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_macd(ticker: str) -> MACDData:
    """Compute MACD data for *ticker*.

    Never raises. Returns MACDData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1y", interval="1d")
    except Exception:
        return MACDData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    if hist.empty or "Close" not in hist.columns:
        return MACDData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 MACD。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()

    if len(close) < _MIN_BARS:
        return MACDData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=(
                f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 MACD。"
            ),
            as_of_date=as_of,
        )

    macd_series, sig_series, hist_series = _compute_macd_series(close)

    macd_val = float(macd_series.iloc[-1])
    sig_val = float(sig_series.iloc[-1])
    hist_val = float(hist_series.iloc[-1])
    prev_hist_val = float(hist_series.iloc[-2]) if len(hist_series) >= 2 else None

    histogram_expanding = (
        prev_hist_val is not None
        and abs(hist_val) > abs(prev_hist_val)
    )

    # Detect recent crossover in last 3 bars
    recent_crossover = False
    crossover_direction = ""
    if len(hist_series) >= 4:
        signs_recent = [1 if v > 0 else (-1 if v < 0 else 0) for v in hist_series.iloc[-4:]]
        for i in range(1, len(signs_recent)):
            prev_s = signs_recent[i - 1]
            curr_s = signs_recent[i]
            if prev_s != 0 and curr_s != 0 and prev_s != curr_s:
                recent_crossover = True
                crossover_direction = "bull" if curr_s > 0 else "bear"
                # Keep the most recent crossover
                break

    macd_score = _compute_macd_score(
        macd_val,
        sig_val,
        hist_val,
        prev_hist_val,
        recent_crossover,
        crossover_direction,
    )
    signal = _classify_signal(macd_score)

    interpretation = _build_interpretation(
        ticker, signal, macd_score,
        macd_val, hist_val,
        recent_crossover, crossover_direction,
    )

    return MACDData(
        ticker=ticker,
        macd=round(macd_val, 4),
        signal_line=round(sig_val, 4),
        histogram=round(hist_val, 4),
        prev_histogram=round(prev_hist_val, 4) if prev_hist_val is not None else None,
        histogram_expanding=histogram_expanding,
        recent_crossover=recent_crossover,
        crossover_direction=crossover_direction,
        macd_score=round(macd_score, 1),
        signal=signal,
        interpretation=interpretation,
        as_of_date=as_of,
        data_available=True,
    )
