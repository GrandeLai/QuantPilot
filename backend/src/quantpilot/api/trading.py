"""统一交易 API.

以 Longbridge 官方模拟账户为主目标，mock provider 仅作为本地兜底。
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query

from quantpilot.broker.provider import get_trading_provider
from quantpilot.broker.types import (
    TradingOrderEstimateRequest,
    TradingOrderRequest,
    TradingProviderError,
)

router = APIRouter(prefix="/trading", tags=["交易"])


def _provider():
    return get_trading_provider()


def _slice_items(items: list[Any], *, page: int, page_size: int) -> dict[str, Any]:
    start = max((page - 1) * page_size, 0)
    end = start + page_size
    return {
        "items": items[start:end],
        "page": page,
        "page_size": page_size,
        "total": len(items),
    }


def _translate_error(exc: TradingProviderError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message})


@router.get("/status")
def get_status() -> dict[str, Any]:
    """返回当前交易 provider 状态与能力边界."""
    status = _provider().get_status()
    return status.model_dump()


@router.get("/securities/search")
def search_securities(
    q: str = Query(default="", min_length=0),
    limit: int = Query(default=20, ge=1, le=50),
) -> dict[str, Any]:
    """按代码 / 名称搜索可交易标的."""
    try:
        items = _provider().search_securities(q, limit=limit)
    except TradingProviderError as exc:
        raise _translate_error(exc) from exc
    return {"items": [item.model_dump() for item in items], "count": len(items)}


@router.get("/quotes")
def get_quotes(symbol: Annotated[list[str] | None, Query()] = None) -> dict[str, Any]:
    """查询标的行情快照."""
    try:
        items = _provider().get_quotes(symbol or [])
    except TradingProviderError as exc:
        raise _translate_error(exc) from exc
    return {"items": [item.model_dump() for item in items], "count": len(items)}


@router.get("/account")
def get_account() -> dict[str, Any]:
    """查询账户总览."""
    try:
        overview = _provider().get_account_overview()
    except TradingProviderError as exc:
        raise _translate_error(exc) from exc
    return overview.model_dump()


@router.get("/positions")
def get_positions() -> dict[str, Any]:
    """查询当前持仓."""
    try:
        items = _provider().get_positions()
    except TradingProviderError as exc:
        raise _translate_error(exc) from exc
    return {"items": [item.model_dump() for item in items], "count": len(items)}


@router.get("/orders/today")
def get_today_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    """查询当日委托."""
    try:
        items = [item.model_dump() for item in _provider().get_today_orders()]
    except TradingProviderError as exc:
        raise _translate_error(exc) from exc
    return _slice_items(items, page=page, page_size=page_size)


@router.get("/orders/history")
def get_history_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    """查询历史委托."""
    try:
        items = [item.model_dump() for item in _provider().get_history_orders()]
    except TradingProviderError as exc:
        raise _translate_error(exc) from exc
    return _slice_items(items, page=page, page_size=page_size)


@router.get("/orders/{order_id}")
def get_order_detail(order_id: str) -> dict[str, Any]:
    """查询订单详情."""
    try:
        detail = _provider().get_order_detail(order_id)
    except TradingProviderError as exc:
        raise _translate_error(exc) from exc
    return detail.model_dump()


@router.post("/orders/estimate")
def estimate_order(req: TradingOrderEstimateRequest) -> dict[str, Any]:
    """下单前估算最大可买 / 可卖数量."""
    try:
        estimate = _provider().estimate_order(req)
    except TradingProviderError as exc:
        raise _translate_error(exc) from exc
    return estimate.model_dump()


@router.post("/orders")
def submit_order(req: TradingOrderRequest) -> dict[str, Any]:
    """提交交易订单."""
    try:
        result = _provider().submit_order(req)
    except TradingProviderError as exc:
        raise _translate_error(exc) from exc
    return result.model_dump()


@router.delete("/orders/{order_id}")
def cancel_order(order_id: str) -> dict[str, Any]:
    """撤销订单."""
    try:
        result = _provider().cancel_order(order_id)
    except TradingProviderError as exc:
        raise _translate_error(exc) from exc
    return result.model_dump()


@router.get("/executions/today")
def get_today_executions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    """查询当日成交."""
    try:
        items = [item.model_dump() for item in _provider().get_today_executions()]
    except TradingProviderError as exc:
        raise _translate_error(exc) from exc
    return _slice_items(items, page=page, page_size=page_size)


@router.get("/executions/history")
def get_history_executions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    """查询历史成交."""
    try:
        items = [item.model_dump() for item in _provider().get_history_executions()]
    except TradingProviderError as exc:
        raise _translate_error(exc) from exc
    return _slice_items(items, page=page, page_size=page_size)


@router.get("/cash-flows")
def get_cash_flows(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    """查询资金流水."""
    try:
        items = [item.model_dump() for item in _provider().get_cash_flows()]
    except TradingProviderError as exc:
        raise _translate_error(exc) from exc
    return _slice_items(items, page=page, page_size=page_size)
