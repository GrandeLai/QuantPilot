"""多策略组合管理 API.

端点:
  POST /portfolio/strategies           添加策略
  GET  /portfolio/strategies           列出所有策略
  DELETE /portfolio/strategies/{name}  移除策略
  GET  /portfolio/summary              组合概览（同时记录历史快照）
  GET  /portfolio/correlation          相关性矩阵
  GET  /portfolio/equity               权益曲线（历史净值序列）
  GET  /portfolio/available-strategies 可加入的模板策略
"""
from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from quantpilot.portfolio.manager import PortfolioManager
from quantpilot.portfolio.snapshots import PortfolioSnapshot, SnapshotStorage, StrategySnapshot

router = APIRouter(prefix="/portfolio", tags=["组合管理"])

_manager = PortfolioManager(total_cash=10_000_000.0)
_storage = SnapshotStorage()
_lock = threading.Lock()


class AddStrategyRequest(BaseModel):
    name: str
    strategy_class: str
    symbol: str
    timeframe: str
    allocation: float
    params: dict[str, Any] = {}


@router.post("/strategies")
def add_strategy(req: AddStrategyRequest) -> dict[str, str]:
    """添加策略到组合."""
    from quantpilot.strategy.loader import load_strategy_class

    cls = load_strategy_class(req.strategy_class)
    if cls is None:
        raise HTTPException(status_code=404, detail=f"策略 '{req.strategy_class}' 未找到")
    try:
        strategy = cls(**req.params)
        _manager.add_strategy(req.name, strategy, req.symbol, req.timeframe, req.allocation)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"message": f"策略 '{req.name}' 已加入组合"}


@router.get("/strategies")
def list_strategies() -> dict[str, Any]:
    """列出所有策略槽位."""
    return {
        "count": len(_manager.strategies),
        "strategies": [
            {
                "name": name,
                "symbol": slot.session.symbol,
                "allocation": slot.allocation,
                "bars_processed": slot.session.bars_processed,
            }
            for name, slot in _manager.strategies.items()
        ],
    }


@router.delete("/strategies/{name}")
def remove_strategy(name: str) -> dict[str, str]:
    """从组合中移除策略."""
    _manager.remove_strategy(name)
    return {"message": f"策略 '{name}' 已移除"}


@router.get("/summary")
def portfolio_summary() -> dict[str, Any]:
    """获取组合总览，同时记录历史快照用于 equity 曲线和 daily_pnl."""
    current_prices = {
        slot.session.symbol: slot.session.positions.get(
            slot.session.symbol,
            type("Pos", (), {"avg_price": 0.0})(),
        ).avg_price
        for slot in _manager.strategies.values()
    }
    summary = _manager.summary(current_prices)

    # 记录快照
    now_iso = datetime.now(timezone.utc).isoformat()
    total_pnl = sum(s["pnl"] for s in summary["strategies"])
    _storage.save_snapshot(
        PortfolioSnapshot(
            timestamp=now_iso,
            total_value=summary["total_portfolio_value"],
            total_cash=summary["total_cash"],
            total_pnl=total_pnl,
        )
    )
    for s in summary["strategies"]:
        _storage.save_strategy_snapshot(
            StrategySnapshot(
                timestamp=now_iso,
                strategy_name=s["name"],
                portfolio_value=s["portfolio_value"],
                pnl=s["pnl"],
                allocation=s["allocation"],
            )
        )

    # 计算 daily_pnl
    snap_24h = _storage.snapshot_24h_ago()
    if snap_24h is not None:
        daily_pnl = summary["total_portfolio_value"] - snap_24h.total_value
        daily_pnl_pct = (
            daily_pnl / snap_24h.total_value * 100 if snap_24h.total_value > 0 else 0.0
        )
    else:
        daily_pnl = 0.0
        daily_pnl_pct = 0.0

    return {
        **summary,
        "daily_pnl": round(daily_pnl, 2),
        "daily_pnl_pct": round(daily_pnl_pct, 4),
    }


@router.get("/equity")
def portfolio_equity(
    period: Literal["1D", "1W", "1M", "ALL"] = Query(default="1M"),
) -> dict[str, Any]:
    """返回权益曲线历史数据（降采样至最多 200 点）."""
    now = datetime.now(timezone.utc)
    since_map: dict[str, datetime | None] = {
        "1D": now - timedelta(days=1),
        "1W": now - timedelta(weeks=1),
        "1M": now - timedelta(days=30),
        "ALL": None,
    }
    since = since_map[period]
    snaps = _storage.list_snapshots(since=since, limit=5000)

    # 降采样：目标最多 200 个点
    if len(snaps) > 200:
        step = len(snaps) // 200
        snaps = snaps[::step]

    points = [
        {
            "timestamp": s.timestamp,
            "value": s.total_value,
            "date": s.timestamp[:10],  # YYYY-MM-DD
        }
        for s in snaps
    ]
    return {"period": period, "points": points, "count": len(points)}


@router.get("/correlation")
def correlation_matrix() -> dict[str, Any]:
    """返回策略净值序列相关性矩阵."""
    return {"correlation": _manager.correlation_matrix()}


@router.get("/available-strategies")
def available_strategies() -> dict[str, Any]:
    """返回可加入组合的模板策略列表（含默认参数）."""
    from quantpilot.strategy.templates import TEMPLATE_STRATEGIES

    return {
        "strategies": [
            {
                "id": sid,
                "name": cls.name,
                "description": cls.description,
                "default_params": cls.default_params,
            }
            for sid, cls in TEMPLATE_STRATEGIES.items()
        ]
    }
