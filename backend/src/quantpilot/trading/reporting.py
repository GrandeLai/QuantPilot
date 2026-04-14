"""Execution-quality reporting for unified trading orders."""

from __future__ import annotations

from datetime import datetime

from quantpilot.broker.types import TradingExecutionReport, TradingOrder, TradingOrderEvent


def build_execution_report(order: TradingOrder, events: list[TradingOrderEvent]) -> TradingExecutionReport:
    """Build a minimal execution report from the order snapshot and event timeline."""
    submitted_quantity = max(order.quantity, 0)
    executed_quantity = max(order.executed_quantity, 0)
    fill_ratio = (executed_quantity / submitted_quantity) if submitted_quantity > 0 else 0.0
    lifecycle_seconds = 0.0
    if events:
      started_at = _parse_iso(events[0].occurred_at)
      ended_at = _parse_iso(events[-1].occurred_at)
      lifecycle_seconds = max((ended_at - started_at).total_seconds(), 0.0)
    price_delta = None
    slippage_bps = None
    if order.submitted_price is not None and order.executed_price is not None:
      price_delta = order.executed_price - order.submitted_price
      if order.submitted_price != 0:
        slippage_bps = (price_delta / order.submitted_price) * 10_000

    return TradingExecutionReport(
        order_id=order.order_id,
        status=order.status,
        submitted_quantity=submitted_quantity,
        executed_quantity=executed_quantity,
        fill_ratio=round(fill_ratio, 6),
        event_count=len(events),
        lifecycle_seconds=round(lifecycle_seconds, 6),
        price_delta=round(price_delta, 6) if price_delta is not None else None,
        slippage_bps=round(slippage_bps, 6) if slippage_bps is not None else None,
    )


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
