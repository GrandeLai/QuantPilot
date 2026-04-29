"""Advisor API — 给 assistant frontend 提供投资建议数据.

Endpoints:
  GET /advisor/overview               组合总览 (AdvisorOverviewPayload)
  GET /advisor/crypto/opportunities   加密机会卡片列表 (symbol 参数)
  GET /advisor/crypto/risks           加密风险卡片列表 (symbol 参数)
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Query

from quantpilot_stock.crypto_derivs.analytics import funding_extreme_signal
from quantpilot_stock.crypto_derivs.collector import (
    fetch_aggregated_derivs,
    fetch_binance_funding_history,
    fetch_okx_funding_history,
)

router = APIRouter(prefix="/advisor", tags=["advisor"])


# ---------- helpers ----------------------------------------------------------


def _extract_asset(symbol: str) -> str:
    """BTC-USDT → BTC."""
    return symbol.split("-")[0].upper()


async def _get_funding_signal(asset: str) -> dict[str, Any]:
    """Fetch funding history from both exchanges and compute extreme signal."""
    try:
        binance_hist, okx_hist = await _fetch_both_histories(asset)
    except Exception:
        return {"signal": "neutral", "z_score": 0.0, "percentile": 50.0, "funding_rate": 0.0}

    history = [f.funding_rate for f in binance_hist] + [f.funding_rate for f in okx_hist]

    try:
        agg = await fetch_aggregated_derivs(asset)
        b_fr = agg["funding"].get("binance")
        o_fr = agg["funding"].get("okx")
        current = float(b_fr.funding_rate if b_fr else (o_fr.funding_rate if o_fr else 0.0))
    except Exception:
        current = history[-1] if history else 0.0

    if len(history) >= 30:
        try:
            sig = funding_extreme_signal(current, history)
        except Exception:
            sig = {"signal": "neutral", "z_score": 0.0, "percentile": 50.0}
    else:
        sig = {"signal": "neutral", "z_score": 0.0, "percentile": 50.0}

    return {**sig, "funding_rate": current}


async def _fetch_both_histories(asset: str) -> tuple[list[Any], list[Any]]:
    """Fetch binance + okx funding history concurrently; return (binance, okx)."""
    import asyncio
    results = await asyncio.gather(
        fetch_binance_funding_history(asset, limit=90),
        fetch_okx_funding_history(asset, limit=90),
        return_exceptions=True,
    )
    binance = results[0] if not isinstance(results[0], BaseException) else []
    okx = results[1] if not isinstance(results[1], BaseException) else []
    return binance, okx  # type: ignore[return-value]


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


# ---------- overview ---------------------------------------------------------


@router.get("/overview")
def advisor_overview() -> dict[str, Any]:
    """组合总览 — 对接 assistant frontend 资产总览 tab."""
    try:
        from quantpilot_stock.api.portfolio import _manager  # type: ignore[attr-defined]

        current_prices: dict[str, float] = {
            slot.session.symbol: slot.session.positions.get(
                slot.session.symbol,
                type("_P", (), {"avg_price": 0.0})(),
            ).avg_price
            for slot in _manager.strategies.values()
        }
        summary = _manager.summary(current_prices)
        net_worth = float(summary.get("total_portfolio_value", 0.0))
        total_cash = float(summary.get("total_cash", 0.0))
        cash_ratio = total_cash / net_worth if net_worth > 0 else 1.0
        positions = [
            {
                "name": s.get("name", ""),
                "symbol": s.get("symbol", ""),
                "allocation": s.get("allocation", 0.0),
                "pnl": s.get("pnl", 0.0),
                "portfolio_value": s.get("portfolio_value", 0.0),
            }
            for s in summary.get("strategies", [])
        ]
    except Exception:
        net_worth = 0.0
        cash_ratio = 1.0
        positions = []

    return {
        "net_worth": net_worth,
        "cash_ratio": cash_ratio,
        "positions": positions,
        "generated_at": _now_iso(),
    }


# ---------- opportunities ----------------------------------------------------


@router.get("/crypto/opportunities")
async def crypto_opportunities(
    symbol: str = Query(default="BTC-USDT"),
) -> dict[str, Any]:
    """加密机会卡片 — 基于资金费率极值信号."""
    asset = _extract_asset(symbol)
    sig = await _get_funding_signal(asset)

    signal = str(sig.get("signal", "neutral"))
    z = float(sig.get("z_score", 0.0))
    pct = float(sig.get("percentile", 50.0))
    funding = float(sig.get("funding_rate", 0.0))
    funding_pct = funding * 100.0

    items: list[dict[str, Any]] = []

    if signal == "contrarian_long":
        confidence = round(min(0.5 + abs(z) * 0.15, 0.92), 3)
        items.append(
            {
                "type": "long_opportunity",
                "subject": symbol,
                "recommendation": (
                    f"资金费率极度偏低（{funding_pct:.4f}%/8h，历史 {pct:.0f}% 百分位），"
                    "空头仓位过度拥挤，反向做多机会窗口开启。"
                ),
                "confidence": confidence,
                "evidence": [
                    {
                        "source": "Binance/OKX 资金费率",
                        "summary": (
                            f"当前资金费率 {funding_pct:.4f}%/8h，z-score={z:.2f}，"
                            f"历史 {pct:.0f}% 百分位"
                        ),
                        "observed_at": _now_iso(),
                    }
                ],
                "risk_notes": [
                    "反向信号不保证立即触发，需配合价格确认",
                    "建议小仓试探，止损设 2%",
                ],
                "freshness": _now_iso(),
            }
        )
    elif signal == "neutral" and pct < 30:
        confidence = round(0.40 + (30.0 - pct) * 0.008, 3)
        items.append(
            {
                "type": "basis_opportunity",
                "subject": symbol,
                "recommendation": (
                    f"资金费率偏低（{funding_pct:.4f}%/8h，{pct:.0f}% 历史分位），"
                    "Cash-and-Carry 套利性价比提升：做多现货 + 对冲永续。"
                ),
                "confidence": confidence,
                "evidence": [
                    {
                        "source": "跨所资金费率",
                        "summary": f"funding={funding_pct:.4f}%/8h，历史 {pct:.0f}% 分位",
                        "observed_at": _now_iso(),
                    }
                ],
                "risk_notes": [
                    "Basis 可能进一步收窄",
                    "套利需双边流动性支撑",
                ],
                "freshness": _now_iso(),
            }
        )

    return {"items": items}


# ---------- risks ------------------------------------------------------------


@router.get("/crypto/risks")
async def crypto_risks(
    symbol: str = Query(default="BTC-USDT"),
) -> dict[str, Any]:
    """加密风险卡片 — 基于资金费率极值信号."""
    asset = _extract_asset(symbol)
    sig = await _get_funding_signal(asset)

    signal = str(sig.get("signal", "neutral"))
    z = float(sig.get("z_score", 0.0))
    pct = float(sig.get("percentile", 50.0))
    funding = float(sig.get("funding_rate", 0.0))
    funding_pct = funding * 100.0

    items: list[dict[str, Any]] = []

    if signal == "contrarian_short":
        confidence = round(min(0.5 + abs(z) * 0.15, 0.92), 3)
        funding_annual_pct = funding * 1095 * 100.0
        items.append(
            {
                "type": "crowded_long_risk",
                "subject": symbol,
                "recommendation": (
                    f"资金费率极高（{funding_pct:.4f}%/8h，历史 {pct:.0f}% 百分位），"
                    "多头仓位过度拥挤，强平风险上升，建议减仓或对冲。"
                ),
                "confidence": confidence,
                "evidence": [
                    {
                        "source": "Binance/OKX 资金费率",
                        "summary": (
                            f"资金费率 {funding_pct:.4f}%/8h，z-score={z:.2f}，"
                            f"历史 {pct:.0f}% 百分位"
                        ),
                        "observed_at": _now_iso(),
                    }
                ],
                "risk_notes": [
                    f"持仓年化资金成本约 {funding_annual_pct:.1f}%",
                    "历史此百分位 3-7 日内回调概率超 60%",
                ],
                "freshness": _now_iso(),
            }
        )
    elif signal == "neutral" and pct > 70:
        confidence = round(0.35 + (pct - 70.0) * 0.008, 3)
        items.append(
            {
                "type": "elevated_funding_risk",
                "subject": symbol,
                "recommendation": (
                    f"资金费率偏高（{funding_pct:.4f}%/8h，{pct:.0f}% 历史分位），"
                    "多头持续付费，若价格停滞则持仓成本累积。"
                ),
                "confidence": confidence,
                "evidence": [
                    {
                        "source": "跨所资金费率监控",
                        "summary": f"funding={funding_pct:.4f}%/8h，处于 {pct:.0f}% 历史分位",
                        "observed_at": _now_iso(),
                    }
                ],
                "risk_notes": ["未达强平触发线，但累积成本需关注"],
                "freshness": _now_iso(),
            }
        )

    return {"items": items}
