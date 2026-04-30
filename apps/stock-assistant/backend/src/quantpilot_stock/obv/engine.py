"""On-Balance Volume (OBV) engine — Phase F.41.

Computes OBV (cumulative volume direction), OBV vs EMA20 trend,
5-day short-term momentum, price-OBV divergence detection,
and composite score (0-100).

Never raises; degrades gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import yfinance as yf

OBVSignal = Literal[
    "strong_bull",
    "bull",
    "neutral",
    "bear",
    "strong_bear",
    "no_data",
]


@dataclass
class OBVData:
    ticker: str
    obv: float | None = None              # Latest OBV value
    obv_ema20: float | None = None        # EMA20 of OBV
    obv_above_ema: bool = False           # OBV > OBV_EMA20
    obv_5d_change_pct: float | None = None  # OBV 5-day % change (normalised)
    price_5d_change_pct: float | None = None  # Price 5-day % change
    price_obv_trend: str = ""             # "confirming_bull" | "confirming_bear" | "diverging_bull" | "diverging_bear" | "neutral"
    obv_score: float = 50.0              # 0-100
    signal: OBVSignal = "no_data"
    interpretation: str = ""
    as_of_date: str = ""
    data_available: bool = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_MIN_BARS = 25   # 20 (EMA20) + 5 (momentum) + guard


def _compute_obv_series(
    close: "pd.Series",   # type: ignore[name-defined]  # noqa: F821
    volume: "pd.Series",  # type: ignore[name-defined]  # noqa: F821
) -> "pd.Series":  # type: ignore[name-defined]  # noqa: F821
    """Return OBV series: cumulative sum of signed volume."""
    delta = close.diff()
    signed_vol = volume.copy().astype(float)
    signed_vol[delta > 0] = volume[delta > 0]
    signed_vol[delta < 0] = -volume[delta < 0]
    signed_vol[delta == 0] = 0.0
    return signed_vol.cumsum()


def _safe_pct_change(new: float, old: float) -> float | None:
    """Return (new - old) / abs(old), or None if old is 0."""
    if old == 0:
        return None
    return (new - old) / abs(old)


def _compute_obv_score(
    obv_above_ema: bool,
    obv_5d_change_pct: float | None,
    price_obv_trend: str,
) -> float:
    """Composite OBV score in [0, 100].

    Raw range [-4, 4]:
      ±2: OBV above/below its EMA20 (primary trend)
      ±1: OBV 5-day momentum direction
      ±1: Price-OBV confirmation/divergence signal
    Map: (raw + 4) / 8 * 100
    """
    raw = 2.0 if obv_above_ema else -2.0

    if obv_5d_change_pct is not None:
        raw += 1.0 if obv_5d_change_pct > 0 else -1.0

    if price_obv_trend in ("confirming_bull",):
        raw += 1.0
    elif price_obv_trend == "confirming_bear":
        raw -= 1.0
    elif price_obv_trend == "diverging_bull":
        raw += 0.5   # OBV up, price down → potential reversal; mild positive
    elif price_obv_trend == "diverging_bear":
        raw -= 0.5   # OBV down, price up → potential reversal; mild negative

    normalized = (raw + 4.0) / 8.0 * 100.0
    return float(max(0.0, min(100.0, normalized)))


def _classify_signal(obv_score: float | None) -> OBVSignal:
    if obv_score is None:
        return "no_data"
    if obv_score >= 80:
        return "strong_bull"
    if obv_score >= 60:
        return "bull"
    if obv_score >= 40:
        return "neutral"
    if obv_score >= 20:
        return "bear"
    return "strong_bear"


def _price_obv_trend(
    price_5d: float | None,
    obv_5d: float | None,
) -> str:
    if price_5d is None or obv_5d is None:
        return "neutral"
    if price_5d > 0 and obv_5d > 0:
        return "confirming_bull"
    if price_5d < 0 and obv_5d < 0:
        return "confirming_bear"
    if price_5d < 0 and obv_5d > 0:
        return "diverging_bull"
    if price_5d > 0 and obv_5d < 0:
        return "diverging_bear"
    return "neutral"


def _build_interpretation(
    ticker: str,
    signal: OBVSignal,
    obv_score: float,
    obv_above_ema: bool,
    price_obv_trend: str,
) -> str:
    labels: dict[OBVSignal, str] = {
        "strong_bull": f"{ticker} OBV 评分 {obv_score:.0f}：量能强势，OBV 远超均线，资金持续流入。",
        "bull": f"{ticker} OBV 评分 {obv_score:.0f}：量能偏多，OBV 高于均线，买盘占优。",
        "neutral": f"{ticker} OBV 评分 {obv_score:.0f}：量能中性，买卖力量均衡。",
        "bear": f"{ticker} OBV 评分 {obv_score:.0f}：量能偏空，OBV 低于均线，卖盘占优。",
        "strong_bear": f"{ticker} OBV 评分 {obv_score:.0f}：量能弱势，OBV 持续下行，资金持续流出。",
        "no_data": f"{ticker} 数据不足，无法计算 OBV。",
    }
    parts = [labels.get(signal, "")]
    trend_map = {
        "confirming_bull": "（OBV 与价格同步上涨，量价配合良好）",
        "confirming_bear": "（OBV 与价格同步下跌，量价配合下行）",
        "diverging_bull": "（OBV 上涨但价格下跌，量能背离看涨）",
        "diverging_bear": "（OBV 下跌但价格上涨，量能背离看跌）",
    }
    if price_obv_trend in trend_map:
        parts.append(trend_map[price_obv_trend])
    if not obv_above_ema and signal not in ("strong_bear", "no_data"):
        parts.append("（OBV 仍在均线下方，需确认突破）")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_obv(ticker: str) -> OBVData:
    """Compute OBV data for *ticker*.

    Never raises. Returns OBVData with data_available=False on hard failure.
    """
    as_of = date.today().isoformat()

    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1y", interval="1d")
    except Exception:
        return OBVData(
            ticker=ticker,
            data_available=False,
            signal="no_data",
            interpretation=f"{ticker} 数据获取失败（yfinance 异常）。",
            as_of_date=as_of,
        )

    if hist.empty or not {"Close", "Volume"}.issubset(hist.columns):
        return OBVData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 历史数据为空，无法计算 OBV。",
            as_of_date=as_of,
        )

    close = hist["Close"].dropna()
    volume = hist["Volume"].dropna()

    # Align
    common_idx = close.index.intersection(volume.index)
    close = close.loc[common_idx]
    volume = volume.loc[common_idx]

    if len(close) < _MIN_BARS:
        return OBVData(
            ticker=ticker,
            data_available=True,
            signal="no_data",
            interpretation=f"{ticker} 数据不足 {_MIN_BARS} 个交易日，无法计算 OBV。",
            as_of_date=as_of,
        )

    obv_series = _compute_obv_series(close, volume)
    obv_ema20 = obv_series.ewm(span=20, adjust=False).mean()

    obv_val = float(obv_series.iloc[-1])
    ema_val = float(obv_ema20.iloc[-1])
    obv_5d_old = float(obv_series.iloc[-6]) if len(obv_series) >= 6 else None
    price_5d_old = float(close.iloc[-6]) if len(close) >= 6 else None

    obv_5d_change = _safe_pct_change(obv_val, obv_5d_old) if obv_5d_old is not None else None
    price_5d_change = _safe_pct_change(float(close.iloc[-1]), price_5d_old) if price_5d_old is not None else None

    obv_above_ema = obv_val > ema_val
    trend = _price_obv_trend(price_5d_change, obv_5d_change)

    obv_score = _compute_obv_score(obv_above_ema, obv_5d_change, trend)
    signal = _classify_signal(obv_score)

    interpretation = _build_interpretation(ticker, signal, obv_score, obv_above_ema, trend)

    return OBVData(
        ticker=ticker,
        obv=round(obv_val, 0),
        obv_ema20=round(ema_val, 0),
        obv_above_ema=obv_above_ema,
        obv_5d_change_pct=round(obv_5d_change, 4) if obv_5d_change is not None else None,
        price_5d_change_pct=round(price_5d_change, 4) if price_5d_change is not None else None,
        price_obv_trend=trend,
        obv_score=round(obv_score, 1),
        signal=signal,
        interpretation=interpretation,
        as_of_date=as_of,
        data_available=True,
    )
