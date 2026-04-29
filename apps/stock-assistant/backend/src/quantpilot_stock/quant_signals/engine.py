"""Quant signals engine — Beneish M-Score + Russell rebalancing preview.

Beneish M-Score:
    8 financial ratios that detect earnings manipulation.
    M > -1.78 → high manipulation risk (manipulator).
    -2.22 ≤ M ≤ -1.78 → grey zone.
    M < -2.22 → likely safe.

    M = -4.840 + 0.920×DSRI + 0.528×GMI + 0.404×AQI + 0.892×SGI
            + 0.115×DEPI - 0.172×SGAI + 4.679×TATA - 0.327×LVGI

Russell Rebalancing Preview:
    Russell 1000 = top 1000 US stocks by market cap.
    Russell 2000 = ranks 1001-3000.
    Annual rebalance in late June — rule-based, predictable.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

import yfinance as yf
from loguru import logger

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class BeneishMScore:
    """Beneish M-Score earnings manipulation signal."""

    ticker: str
    m_score: float  # < -2.22 safe; -2.22 ~ -1.78 grey; > -1.78 high risk
    risk_level: Literal["safe", "grey", "manipulator"]
    ratios: dict[str, float]  # 8 financial ratio details
    interpretation: str
    as_of_date: date


@dataclass
class RussellMembership:
    """Russell index membership estimation and rebalancing signal."""

    ticker: str
    market_cap_usd: float
    estimated_rank: int | None  # estimated rank among all US stocks by market cap
    current_index: Literal[
        "Russell 1000", "Russell 2000", "Outside Russell 3000", "Unknown"
    ]
    proximity_score: float  # 0-1, how close to the 1000/2000 boundary (higher = closer)
    rebalance_signal: Literal[
        "likely_add_1000",
        "likely_drop_1000",
        "likely_add_2000",
        "likely_drop_2000",
        "stable",
        "unknown",
    ]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe_div(num: float, den: float, default: float = 1.0) -> float:
    """Safe division that returns *default* when denominator is zero or NaN."""
    if den == 0 or not math.isfinite(den) or not math.isfinite(num):
        return default
    return num / den


def _risk_level(m: float) -> Literal["safe", "grey", "manipulator"]:
    if m < -2.22:
        return "safe"
    if m <= -1.78:
        return "grey"
    return "manipulator"


def _interpretation(m: float, risk: Literal["safe", "grey", "manipulator"]) -> str:
    msgs = {
        "safe": f"M-Score {m:.3f} < -2.22：财务健康，盈利操纵风险低。",
        "grey": f"M-Score {m:.3f} 介于 -2.22~-1.78：灰色区域，需结合其他指标判断。",
        "manipulator": f"M-Score {m:.3f} > -1.78：⚠ 高操纵风险，历史上此区间股票后续跑输市场。",
    }
    return msgs[risk]


# ---------------------------------------------------------------------------
# Beneish M-Score computation
# ---------------------------------------------------------------------------

def compute_beneish_mscore(ticker: str) -> BeneishMScore | None:
    """Compute Beneish M-Score (8-dimension earnings manipulation detector).

    Returns None if insufficient financial data is available.
    """
    try:
        t = yf.Ticker(ticker)
        income = t.financials        # columns are dates (most recent first)
        balance = t.balance_sheet
        cashflow = t.cashflow

        if income is None or income.empty:
            logger.warning(f"[Beneish] {ticker}: no income statement data")
            return None
        if balance is None or balance.empty:
            logger.warning(f"[Beneish] {ticker}: no balance sheet data")
            return None
        if cashflow is None or cashflow.empty:
            logger.warning(f"[Beneish] {ticker}: no cash flow data")
            return None

        # Need at least 2 periods for ratio changes
        if income.shape[1] < 2 or balance.shape[1] < 2:
            logger.warning(f"[Beneish] {ticker}: need ≥2 periods, got income={income.shape[1]}")
            return None

        def _get(df, key: str, col: int, default: float = 0.0) -> float:
            try:
                if key in df.index:
                    val = df.loc[key].iloc[col]
                    return float(val) if val is not None and math.isfinite(float(val)) else default
            except Exception:
                pass
            return default

        # Income statement items (col 0 = most recent, col 1 = prior year)
        revenue_t  = _get(income, "Total Revenue", 0)
        revenue_t1 = _get(income, "Total Revenue", 1)
        cogs_t     = _get(income, "Cost Of Revenue", 0)
        cogs_t1    = _get(income, "Cost Of Revenue", 1)
        sga_t      = _get(income, "Selling General Administrative", 0)
        sga_t1     = _get(income, "Selling General Administrative", 1)
        ni_t       = _get(income, "Net Income", 0)
        dep_t      = _get(cashflow, "Depreciation", 0)
        dep_t1     = _get(cashflow, "Depreciation", 1)
        cfo_t      = _get(cashflow, "Operating Cash Flow", 0)

        # Balance sheet items
        ar_t   = _get(balance, "Net Receivables", 0)
        ar_t1  = _get(balance, "Net Receivables", 1)
        ppe_t  = _get(balance, "Net PPE", 0)
        ppe_t1 = _get(balance, "Net PPE", 1)
        ta_t   = _get(balance, "Total Assets", 0)
        ta_t1  = _get(balance, "Total Assets", 1)
        ca_t   = _get(balance, "Current Assets", 0)
        ca_t1  = _get(balance, "Current Assets", 1)
        ltd_t  = _get(balance, "Long Term Debt", 0)
        ltd_t1 = _get(balance, "Long Term Debt", 1)
        cl_t   = _get(balance, "Current Liabilities", 0)
        cl_t1  = _get(balance, "Current Liabilities", 1)

        # Guard: need non-zero revenue to compute any ratio
        if revenue_t == 0 or revenue_t1 == 0 or ta_t == 0:
            logger.warning(f"[Beneish] {ticker}: zero revenue or total assets")
            return None

        # --- 8 Beneish Ratios ---

        # 1. DSRI: Days Sales Receivable Index
        dsri_t  = _safe_div(ar_t, revenue_t)
        dsri_t1 = _safe_div(ar_t1, revenue_t1)
        DSRI = _safe_div(dsri_t, dsri_t1)

        # 2. GMI: Gross Margin Index  (prior / current)
        gm_t  = _safe_div(revenue_t  - cogs_t,  revenue_t)
        gm_t1 = _safe_div(revenue_t1 - cogs_t1, revenue_t1)
        GMI = _safe_div(gm_t1, gm_t)

        # 3. AQI: Asset Quality Index
        aqi_t  = 1 - _safe_div(ca_t  + ppe_t,  ta_t)
        aqi_t1 = 1 - _safe_div(ca_t1 + ppe_t1, ta_t1)
        AQI = _safe_div(aqi_t, aqi_t1)

        # 4. SGI: Sales Growth Index
        SGI = _safe_div(revenue_t, revenue_t1)

        # 5. DEPI: Depreciation Index  (prior / current depreciation rate)
        dep_rate_t  = _safe_div(dep_t,  dep_t  + ppe_t)
        dep_rate_t1 = _safe_div(dep_t1, dep_t1 + ppe_t1)
        DEPI = _safe_div(dep_rate_t1, dep_rate_t)

        # 6. SGAI: SGA Index
        sgai_t  = _safe_div(sga_t,  revenue_t)
        sgai_t1 = _safe_div(sga_t1, revenue_t1)
        SGAI = _safe_div(sgai_t, sgai_t1)

        # 7. LVGI: Leverage Index
        lev_t  = _safe_div(ltd_t  + cl_t,  ta_t)
        lev_t1 = _safe_div(ltd_t1 + cl_t1, ta_t1)
        LVGI = _safe_div(lev_t, lev_t1)

        # 8. TATA: Total Accruals to Total Assets
        TATA = _safe_div(ni_t - cfo_t, ta_t)

        # --- M-Score formula ---
        m_score = (
            -4.840
            + 0.920 * DSRI
            + 0.528 * GMI
            + 0.404 * AQI
            + 0.892 * SGI
            + 0.115 * DEPI
            - 0.172 * SGAI
            + 4.679 * TATA
            - 0.327 * LVGI
        )

        ratios: dict[str, float] = {
            "DSRI": round(DSRI, 4),
            "GMI":  round(GMI,  4),
            "AQI":  round(AQI,  4),
            "SGI":  round(SGI,  4),
            "DEPI": round(DEPI, 4),
            "SGAI": round(SGAI, 4),
            "LVGI": round(LVGI, 4),
            "TATA": round(TATA, 4),
        }

        risk = _risk_level(m_score)
        interp = _interpretation(m_score, risk)

        # as_of_date from the most recent income statement column
        try:
            col_date = income.columns[0]
            as_of = col_date.date() if hasattr(col_date, "date") else date.today()
        except Exception:
            as_of = date.today()

        return BeneishMScore(
            ticker=ticker.upper(),
            m_score=round(m_score, 4),
            risk_level=risk,
            ratios=ratios,
            interpretation=interp,
            as_of_date=as_of,
        )

    except Exception as exc:
        logger.error(f"[Beneish] {ticker} error: {exc}")
        return None


# ---------------------------------------------------------------------------
# Russell membership estimation
# ---------------------------------------------------------------------------

# Approximate market cap boundaries for Russell index membership (USD).
# These thresholds are derived from FTSE Russell's public methodology:
#   - Russell 3000 = top 3000 US stocks by total market cap
#   - Russell 1000 = top 1000 within Russell 3000
#   - Russell 2000 = ranks 1001-3000 within Russell 3000
# Boundaries shift year to year; these are representative approximations.
_RUSSELL_1000_MIN_CAP_USD = 5_000_000_000    # ~$5B (lower bound for Russell 1000)
_RUSSELL_2000_MIN_CAP_USD = 200_000_000      # ~$200M (lower bound for Russell 2000)
_RUSSELL_3000_MIN_CAP_USD = 100_000_000      # ~$100M (minimum for Russell 3000 inclusion)

# Boundary proximity bands (how close to the 1000/2000 cut line → high proximity score)
_R1000_BOUNDARY_BAND = 0.20   # within ±20% of the boundary cap → high proximity
_R2000_BOUNDARY_BAND = 0.25

# Approximate R1000/R2000 boundary market cap
_R1000_BOUNDARY_CAP = 6_500_000_000   # ~$6.5B is historically near rank 1000
_R2000_BOUNDARY_CAP = 350_000_000     # ~$350M is historically near rank 2000/3000


def _estimate_rank_from_cap(market_cap: float) -> int | None:
    """Estimate market cap rank using a log-linear interpolation model.

    Based on approximate power-law distribution of US stock market caps.
    """
    if market_cap <= 0:
        return None
    # Simple segmented approximation:
    #   rank 1-10:     cap > $1T
    #   rank 10-100:   $100B-$1T
    #   rank 100-500:  $20B-$100B
    #   rank 500-1000: $5B-$20B
    #   rank 1000-2000:$1B-$5B
    #   rank 2000-3000:$200M-$1B
    #   rank 3000+:    <$200M
    cap = market_cap
    if cap >= 1_000_000_000_000:
        return max(1, int(10 * (1_000_000_000_000 / cap) ** 0.5))
    if cap >= 100_000_000_000:
        return int(10 + 90 * (1 - (cap - 100e9) / 900e9))
    if cap >= 20_000_000_000:
        return int(100 + 400 * (1 - (cap - 20e9) / 80e9))
    if cap >= 5_000_000_000:
        return int(500 + 500 * (1 - (cap - 5e9) / 15e9))
    if cap >= 1_000_000_000:
        return int(1000 + 1000 * (1 - (cap - 1e9) / 4e9))
    if cap >= 200_000_000:
        return int(2000 + 1000 * (1 - (cap - 0.2e9) / 0.8e9))
    return 3000 + int(1000 * max(0, 1 - cap / 200e6))


def _proximity_score(market_cap: float, current_index: str) -> float:
    """Compute 0-1 proximity score to the nearest index boundary."""
    if current_index == "Russell 1000":
        ratio = abs(market_cap - _R1000_BOUNDARY_CAP) / _R1000_BOUNDARY_CAP
        return max(0.0, min(1.0, 1.0 - ratio / _R1000_BOUNDARY_BAND))
    if current_index == "Russell 2000":
        # Closer to 1000/2000 cut
        r1_ratio = abs(market_cap - _R1000_BOUNDARY_CAP) / _R1000_BOUNDARY_CAP
        r2_ratio = abs(market_cap - _R2000_BOUNDARY_CAP) / _R2000_BOUNDARY_CAP
        min_ratio = min(r1_ratio, r2_ratio)
        return max(0.0, min(1.0, 1.0 - min_ratio / _R2000_BOUNDARY_BAND))
    return 0.0


def _rebalance_signal(
    market_cap: float,
    rank: int | None,
    current_index: str,
) -> Literal[
    "likely_add_1000",
    "likely_drop_1000",
    "likely_add_2000",
    "likely_drop_2000",
    "stable",
    "unknown",
]:
    if rank is None or current_index == "Unknown":
        return "unknown"

    # Near the R1000/R2000 boundary
    if current_index == "Russell 2000":
        if market_cap >= _R1000_BOUNDARY_CAP * 0.90:  # within 10% of R1000 floor
            return "likely_add_1000"
    if current_index == "Russell 1000":
        if market_cap <= _R1000_BOUNDARY_CAP * 1.10:  # within 10% above R1000 floor
            return "likely_drop_1000"

    # Near the R2000/non-Russell boundary
    if current_index == "Russell 2000":
        if market_cap <= _R2000_BOUNDARY_CAP * 1.15:
            return "likely_drop_2000"
    if current_index == "Outside Russell 3000":
        if market_cap >= _R2000_BOUNDARY_CAP * 0.85:
            return "likely_add_2000"

    return "stable"


def estimate_russell_membership(
    ticker: str,
    *,
    universe_tickers: list[str] | None = None,  # noqa: ARG001 — reserved for future use
) -> RussellMembership | None:
    """Estimate Russell index membership and boundary proximity.

    Uses market cap from yfinance to determine likely Russell 1000/2000/3000
    membership and whether the stock is near a rebalancing boundary.

    *universe_tickers* is accepted for API compatibility but currently unused;
    the rank is estimated from the market-cap distribution model.
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info

        if not info:
            logger.warning(f"[Russell] {ticker}: no info returned")
            return None

        # Market cap (prefer marketCap, fall back to enterpriseValue)
        market_cap = info.get("marketCap") or info.get("enterpriseValue") or 0
        if not market_cap or market_cap <= 0:
            logger.warning(f"[Russell] {ticker}: no market cap data")
            return None

        market_cap = float(market_cap)

        # Determine current index
        if market_cap >= _RUSSELL_1000_MIN_CAP_USD:
            current_index: Literal[
                "Russell 1000", "Russell 2000", "Outside Russell 3000", "Unknown"
            ] = "Russell 1000"
        elif market_cap >= _RUSSELL_2000_MIN_CAP_USD:
            current_index = "Russell 2000"
        elif market_cap >= _RUSSELL_3000_MIN_CAP_USD:
            current_index = "Outside Russell 3000"
        else:
            current_index = "Outside Russell 3000"

        rank = _estimate_rank_from_cap(market_cap)
        prox = _proximity_score(market_cap, current_index)
        signal = _rebalance_signal(market_cap, rank, current_index)

        return RussellMembership(
            ticker=ticker.upper(),
            market_cap_usd=market_cap,
            estimated_rank=rank,
            current_index=current_index,
            proximity_score=round(prox, 4),
            rebalance_signal=signal,
        )

    except Exception as exc:
        logger.error(f"[Russell] {ticker} error: {exc}")
        return None
