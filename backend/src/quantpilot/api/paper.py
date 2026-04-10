"""Paper Trading API — 模拟盘管理接口.

端点:
  POST /paper/sessions          创建模拟盘会话
  GET  /paper/sessions          列出所有会话
  GET  /paper/sessions/{id}     获取会话状态
  DELETE /paper/sessions/{id}   删除会话
"""
from __future__ import annotations

import threading
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from quantpilot.paper.engine import PaperSession, PaperTradingEngine

router = APIRouter(prefix="/paper", tags=["模拟盘"])

_sessions: dict[str, tuple[PaperSession, PaperTradingEngine]] = {}
_lock = threading.Lock()


class CreateSessionRequest(BaseModel):
    session_id: str
    symbol: str
    timeframe: str
    initial_cash: float = 1_000_000.0
    commission_rate: float = 0.001
    slippage_pct: float = 0.0005


@router.post("/sessions")
def create_session(req: CreateSessionRequest) -> dict[str, Any]:
    with _lock:
        if req.session_id in _sessions:
            raise HTTPException(status_code=409, detail=f"会话已存在: {req.session_id}")
        sess = PaperSession(symbol=req.symbol, timeframe=req.timeframe, initial_cash=req.initial_cash)
        engine = PaperTradingEngine(sess, commission_rate=req.commission_rate, slippage_pct=req.slippage_pct)
        _sessions[req.session_id] = (sess, engine)
    return {"session_id": req.session_id, "status": "created", "initial_cash": req.initial_cash}


@router.get("/sessions")
def list_sessions() -> dict[str, Any]:
    with _lock:
        return {
            "sessions": [
                {"session_id": sid, "symbol": s.symbol, "timeframe": s.timeframe, "bars_processed": s.bars_processed}
                for sid, (s, _) in _sessions.items()
            ]
        }


@router.get("/sessions/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    with _lock:
        if session_id not in _sessions:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")
        sess, _ = _sessions[session_id]
    current_prices = {sym: pos.avg_price for sym, pos in sess.positions.items()}
    return {
        "session_id": session_id,
        "symbol": sess.symbol,
        "timeframe": sess.timeframe,
        "cash": sess.cash,
        "portfolio_value": sess.portfolio_value(current_prices),
        "positions": {sym: {"quantity": pos.quantity, "avg_price": pos.avg_price} for sym, pos in sess.positions.items()},
        "trades_count": len(sess.trades),
        "bars_processed": sess.bars_processed,
        "started_at": sess.started_at.isoformat(),
        "last_bar_at": sess.last_bar_at.isoformat() if sess.last_bar_at else None,
    }


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str) -> dict[str, str]:
    with _lock:
        if session_id not in _sessions:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")
        del _sessions[session_id]
    return {"message": f"会话 {session_id} 已删除"}


class ManualOrderRequest(BaseModel):
    symbol: str
    side: str  # "buy" | "sell"
    quantity: int
    price: float  # 前端传入当前价格，用于直接撮合


@router.post("/sessions/{session_id}/orders")
def execute_manual_order(session_id: str, req: ManualOrderRequest) -> dict[str, Any]:
    """直接执行手动订单（无需 Redis，适合 UI 下单面板使用）.

    以传入的 price 为成交价，直接更新 PaperSession 资金和持仓。
    """
    from quantpilot.strategy.base import Order, OrderSide

    with _lock:
        if session_id not in _sessions:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")
        sess, engine = _sessions[session_id]

    side = OrderSide.BUY if req.side.lower() == "buy" else OrderSide.SELL
    fill_price = req.price * (1 + engine._slippage_pct) if side == OrderSide.BUY else req.price * (1 - engine._slippage_pct)
    trade_value = fill_price * req.quantity
    commission = max(engine._commission_rate * trade_value, engine._min_commission)

    with _lock:
        if side == OrderSide.BUY:
            total_cost = trade_value + commission
            if total_cost > sess.cash:
                raise HTTPException(status_code=400, detail="资金不足")
            sess.cash -= total_cost
            existing = sess.positions.get(req.symbol)
            if existing is None:
                from quantpilot.strategy.base import Position
                sess.positions[req.symbol] = Position(
                    symbol=req.symbol, quantity=req.quantity, avg_price=fill_price
                )
            else:
                total_qty = existing.quantity + req.quantity
                existing.avg_price = (existing.avg_price * existing.quantity + fill_price * req.quantity) / total_qty
                existing.quantity = total_qty
        else:
            existing = sess.positions.get(req.symbol)
            if existing is None or existing.quantity < req.quantity:
                raise HTTPException(status_code=400, detail="持仓不足")
            proceeds = trade_value - commission
            entry_price = existing.avg_price
            existing.quantity -= req.quantity
            if existing.quantity == 0:
                del sess.positions[req.symbol]
            sess.cash += proceeds
            from quantpilot.backtest.metrics import TradeRecord
            from datetime import UTC, datetime
            sess.trades.append(TradeRecord(
                symbol=req.symbol, side="sell",
                entry_time=sess.started_at, exit_time=datetime.now(tz=UTC),
                entry_price=entry_price, exit_price=fill_price,
                quantity=req.quantity, commission=commission,
            ))

    current_prices = {sym: pos.avg_price for sym, pos in sess.positions.items()}
    return {
        "status": "executed",
        "side": req.side,
        "symbol": req.symbol,
        "quantity": req.quantity,
        "fill_price": round(fill_price, 4),
        "commission": round(commission, 4),
        "cash_after": round(sess.cash, 2),
        "portfolio_value": round(sess.portfolio_value(current_prices), 2),
    }


@router.post("/sessions/{session_id}/orders/enqueue")
async def enqueue_order(session_id: str, req: dict[str, Any]) -> dict[str, str]:
    """提交订单到 Redis 订单队列.

    Request body: {"symbol": "AAPL", "side": "buy", "quantity": 10, "price": 150.0, "reason": ""}
    """
    from quantpilot.redis.client import RedisClient
    from quantpilot.redis.order_queue import OrderQueue, QueuedOrder

    if RedisClient._instance is None:
        raise HTTPException(status_code=503, detail="Redis 未连接")
    with _lock:
        if session_id not in _sessions:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")

    order = QueuedOrder(
        session_id=session_id,
        symbol=req.get("symbol", ""),
        side=req.get("side", "buy"),
        quantity=int(req.get("quantity", 0)),
        price=float(req.get("price", 0.0)),
        reason=req.get("reason", ""),
    )
    q = OrderQueue(session_id)
    entry_id = await q.enqueue(order)
    return {"entry_id": entry_id, "message": f"订单已入队: {order.side} {order.symbol}"}


@router.get("/sessions/{session_id}/orders/queue")
async def get_order_queue(session_id: str, count: int = 20) -> dict[str, Any]:
    """查看指定 session 的订单队列."""
    from quantpilot.redis.client import RedisClient
    from quantpilot.redis.order_queue import OrderQueue

    if RedisClient._instance is None:
        raise HTTPException(status_code=503, detail="Redis 未连接")
    q = OrderQueue(session_id)
    orders = await q.dequeue(count=count)
    length = await q.length()
    return {
        "session_id": session_id,
        "total": length,
        "orders": [
            {
                "entry_id": o.entry_id,
                "symbol": o.symbol,
                "side": o.side,
                "quantity": o.quantity,
                "price": o.price,
                "timestamp": o.timestamp,
            }
            for o in orders
        ],
    }
