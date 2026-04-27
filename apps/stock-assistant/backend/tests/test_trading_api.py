"""交易 API 回归测试 — Longbridge-first / mock-fallback."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_trading_provider(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """强制交易层使用 mock provider，便于本地闭环验证."""
    monkeypatch.setenv("QUANTPILOT_TRADING_PROVIDER", "mock")

    from quantpilot_stock.broker.provider import get_trading_provider

    get_trading_provider.cache_clear()
    yield client
    get_trading_provider.cache_clear()


def test_trading_status_exposes_longbridge_boundaries(mock_trading_provider: TestClient) -> None:
    """状态接口应显式暴露当前 provider 与官方能力边界."""
    response = mock_trading_provider.get("/api/trading/status")
    assert response.status_code == 200

    body = response.json()
    assert body["provider"] == "mock"
    assert body["mode"] == "paper"
    assert body["capabilities"]["supports_options"] is False
    assert body["capabilities"]["supports_otc"] is False
    assert body["capabilities"]["supports_us_prepost"] is False


def test_security_search_supports_code_and_name(mock_trading_provider: TestClient) -> None:
    """搜索应支持代码和名称匹配."""
    by_code = mock_trading_provider.get("/api/trading/securities/search?q=AAPL")
    assert by_code.status_code == 200
    assert any(item["symbol"] == "AAPL.US" for item in by_code.json()["items"])

    by_name = mock_trading_provider.get("/api/trading/securities/search?q=apple")
    assert by_name.status_code == 200
    assert any(item["symbol"] == "AAPL.US" for item in by_name.json()["items"])


def test_trading_order_lifecycle_with_mock_provider(mock_trading_provider: TestClient) -> None:
    """完成账户 → 下单 → 委托 / 成交 / 持仓 / 资金 的主闭环."""
    account_before = mock_trading_provider.get("/api/trading/account")
    assert account_before.status_code == 200
    available_before = account_before.json()["available_cash"]

    quote_resp = mock_trading_provider.get("/api/trading/quotes", params=[("symbol", "AAPL.US")])
    assert quote_resp.status_code == 200
    assert quote_resp.json()["items"][0]["symbol"] == "AAPL.US"

    estimate_resp = mock_trading_provider.post(
        "/api/trading/orders/estimate",
        json={"symbol": "AAPL.US", "side": "buy", "order_type": "market"},
    )
    assert estimate_resp.status_code == 200
    assert estimate_resp.json()["cash_max_qty"] > 0

    submit_resp = mock_trading_provider.post(
        "/api/trading/orders",
        json={
            "symbol": "AAPL.US",
            "side": "buy",
            "order_type": "market",
            "quantity": 10,
        },
    )
    assert submit_resp.status_code == 200
    submitted = submit_resp.json()
    assert submitted["status"] == "filled"

    executions_resp = mock_trading_provider.get("/api/trading/executions/today")
    assert executions_resp.status_code == 200
    assert any(item["symbol"] == "AAPL.US" for item in executions_resp.json()["items"])

    positions_resp = mock_trading_provider.get("/api/trading/positions")
    assert positions_resp.status_code == 200
    assert any(item["symbol"] == "AAPL.US" for item in positions_resp.json()["items"])

    account_after = mock_trading_provider.get("/api/trading/account")
    assert account_after.status_code == 200
    assert account_after.json()["available_cash"] < available_before

    cash_flow_resp = mock_trading_provider.get("/api/trading/cash-flows")
    assert cash_flow_resp.status_code == 200
    assert len(cash_flow_resp.json()["items"]) >= 1


def test_limit_order_can_be_canceled_in_mock_provider(mock_trading_provider: TestClient) -> None:
    """未成交限价单应可出现在委托列表中并支持撤单."""
    submit_resp = mock_trading_provider.post(
        "/api/trading/orders",
        json={
            "symbol": "AAPL.US",
            "side": "buy",
            "order_type": "limit",
            "quantity": 10,
            "submitted_price": 1.0,
        },
    )
    assert submit_resp.status_code == 200
    order_id = submit_resp.json()["order_id"]
    assert submit_resp.json()["status"] == "submitted"

    today_orders_resp = mock_trading_provider.get("/api/trading/orders/today")
    assert today_orders_resp.status_code == 200
    assert any(item["order_id"] == order_id for item in today_orders_resp.json()["items"])

    cancel_resp = mock_trading_provider.delete(f"/api/trading/orders/{order_id}")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "canceled"

    detail_resp = mock_trading_provider.get(f"/api/trading/orders/{order_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["status"] == "canceled"

    events_resp = mock_trading_provider.get(f"/api/trading/orders/{order_id}/events")
    assert events_resp.status_code == 200
    events = events_resp.json()["items"]
    assert [item["event_type"] for item in events] == ["submitted", "canceled"]


def test_order_rejected_when_max_order_value_exceeded(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """统一 trading 主线应在提交前执行最大单笔金额风控."""
    monkeypatch.setenv("QUANTPILOT_TRADING_PROVIDER", "mock")
    monkeypatch.setenv("QUANTPILOT_TRADING_RISK_MAX_ORDER_VALUE", "1000")

    from quantpilot_stock.broker.provider import get_trading_provider

    get_trading_provider.cache_clear()

    response = client.post(
        "/api/trading/orders",
        json={
            "symbol": "AAPL.US",
            "side": "buy",
            "order_type": "market",
            "quantity": 10,
        },
    )

    assert response.status_code == 409
    body = response.json()
    assert body["detail"]["code"] == "risk_rejected"
    assert "单笔交易金额" in body["detail"]["message"]


def test_order_rejected_when_daily_loss_limit_exceeded(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """账户当日亏损超过阈值时应前置熔断，拒绝新买单."""
    monkeypatch.setenv("QUANTPILOT_TRADING_PROVIDER", "mock")
    monkeypatch.setenv("QUANTPILOT_TRADING_RISK_DAILY_LOSS_LIMIT_PCT", "0.05")

    from quantpilot_stock.broker.mock import MockTradingProvider
    from quantpilot_stock.broker.provider import get_trading_provider

    original_get_account = MockTradingProvider.get_account_overview

    def _patched_get_account(self: MockTradingProvider):  # type: ignore[override]
        overview = original_get_account(self)
        overview.today_pnl_pct = -0.06
        overview.today_pnl = -6000.0
        return overview

    monkeypatch.setattr(MockTradingProvider, "get_account_overview", _patched_get_account)
    get_trading_provider.cache_clear()

    response = client.post(
        "/api/trading/orders",
        json={
            "symbol": "AAPL.US",
            "side": "buy",
            "order_type": "market",
            "quantity": 1,
        },
    )

    assert response.status_code == 409
    body = response.json()
    assert body["detail"]["code"] == "risk_rejected"
    assert "日内亏损" in body["detail"]["message"]


def test_market_order_events_capture_submit_and_fill(mock_trading_provider: TestClient) -> None:
    """最小 OMS 应为即时成交订单保留提交与成交事件时间线."""
    submit_resp = mock_trading_provider.post(
        "/api/trading/orders",
        json={
            "symbol": "AAPL.US",
            "side": "buy",
            "order_type": "market",
            "quantity": 5,
        },
    )
    assert submit_resp.status_code == 200
    order_id = submit_resp.json()["order_id"]

    events_resp = mock_trading_provider.get(f"/api/trading/orders/{order_id}/events")
    assert events_resp.status_code == 200
    events = events_resp.json()["items"]
    assert [item["event_type"] for item in events] == ["submitted", "filled"]
    assert events[-1]["status"] == "filled"


def test_order_detail_refresh_backfills_provider_status_transition(
    mock_trading_provider: TestClient,
) -> None:
    """读取订单详情时应把 provider 侧新状态同步回 OMS 事件账本."""
    from quantpilot_stock.broker.provider import get_trading_provider
    from quantpilot_stock.broker.types import TradingOrderStatus

    submit_resp = mock_trading_provider.post(
        "/api/trading/orders",
        json={
            "symbol": "AAPL.US",
            "side": "buy",
            "order_type": "limit",
            "quantity": 5,
            "submitted_price": 1.0,
        },
    )
    assert submit_resp.status_code == 200
    order_id = submit_resp.json()["order_id"]

    provider = get_trading_provider()
    order = provider.get_order_detail(order_id)
    order.status = TradingOrderStatus.FILLED
    order.executed_quantity = order.quantity
    order.executed_price = 192.84
    order.updated_at = "2026-04-14T12:00:00+00:00"
    order.message = "provider sync filled"

    detail_resp = mock_trading_provider.get(f"/api/trading/orders/{order_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["status"] == "filled"

    events_resp = mock_trading_provider.get(f"/api/trading/orders/{order_id}/events")
    assert events_resp.status_code == 200
    assert [item["event_type"] for item in events_resp.json()["items"]] == ["submitted", "filled"]


def test_large_market_order_transitions_from_partial_fill_to_filled(
    mock_trading_provider: TestClient,
) -> None:
    """大额市价单应先进入 partial_filled，再在后续刷新中补齐成交。"""
    submit_resp = mock_trading_provider.post(
        "/api/trading/orders",
        json={
            "symbol": "AAPL.US",
            "side": "buy",
            "order_type": "market",
            "quantity": 200,
        },
    )
    assert submit_resp.status_code == 200
    order_id = submit_resp.json()["order_id"]
    assert submit_resp.json()["status"] == "partial_filled"

    initial_detail = mock_trading_provider.get(f"/api/trading/orders/{order_id}")
    assert initial_detail.status_code == 200
    assert initial_detail.json()["status"] == "filled"

    events_resp = mock_trading_provider.get(f"/api/trading/orders/{order_id}/events")
    assert events_resp.status_code == 200
    assert [item["event_type"] for item in events_resp.json()["items"]] == [
        "submitted",
        "partial_filled",
        "filled",
    ]


def test_order_execution_report_summarizes_fill_ratio_and_lifecycle(
    mock_trading_provider: TestClient,
) -> None:
    """订单执行报告应提供成交率、生命周期和事件数摘要."""
    submit_resp = mock_trading_provider.post(
        "/api/trading/orders",
        json={
            "symbol": "AAPL.US",
            "side": "buy",
            "order_type": "limit",
            "quantity": 10,
            "submitted_price": 1.0,
        },
    )
    assert submit_resp.status_code == 200
    order_id = submit_resp.json()["order_id"]

    report_resp = mock_trading_provider.get(f"/api/trading/orders/{order_id}/report")
    assert report_resp.status_code == 200
    report = report_resp.json()

    assert report["order_id"] == order_id
    assert report["fill_ratio"] == 0.0
    assert report["event_count"] >= 1
    assert report["lifecycle_seconds"] >= 0.0
    assert report["submitted_quantity"] == 10
    assert report["execution_count"] == 0


def test_trading_risk_status_exposes_thresholds_and_halt_state(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """交易风控状态接口应返回当前阈值与是否已触发熔断."""
    monkeypatch.setenv("QUANTPILOT_TRADING_PROVIDER", "mock")
    monkeypatch.setenv("QUANTPILOT_TRADING_RISK_MAX_ORDER_VALUE", "5000")
    monkeypatch.setenv("QUANTPILOT_TRADING_RISK_DAILY_LOSS_LIMIT_PCT", "0.05")

    from quantpilot_stock.broker.mock import MockTradingProvider
    from quantpilot_stock.broker.provider import get_trading_provider

    original_get_account = MockTradingProvider.get_account_overview

    def _patched_get_account(self: MockTradingProvider):  # type: ignore[override]
        overview = original_get_account(self)
        overview.today_pnl_pct = -0.06
        overview.today_pnl = -6000.0
        return overview

    monkeypatch.setattr(MockTradingProvider, "get_account_overview", _patched_get_account)
    get_trading_provider.cache_clear()

    response = client.get("/api/trading/risk")
    assert response.status_code == 200
    body = response.json()
    assert body["enabled"] is True
    assert body["halted"] is True
    assert body["max_order_value"] == 5000.0
    assert body["daily_loss_limit_pct"] == 0.05
    assert body["current_today_pnl_pct"] == -0.06
    assert body["open_position_count"] >= 0
    assert "largest_position_symbol" in body


def test_execution_report_includes_multi_fill_details(mock_trading_provider: TestClient) -> None:
    """部分成交订单的执行报告应展示 execution 维度摘要."""
    submit_resp = mock_trading_provider.post(
        "/api/trading/orders",
        json={
            "symbol": "AAPL.US",
            "side": "buy",
            "order_type": "market",
            "quantity": 200,
        },
    )
    assert submit_resp.status_code == 200
    order_id = submit_resp.json()["order_id"]

    detail_resp = mock_trading_provider.get(f"/api/trading/orders/{order_id}")
    assert detail_resp.status_code == 200

    report_resp = mock_trading_provider.get(f"/api/trading/orders/{order_id}/report")
    assert report_resp.status_code == 200
    report = report_resp.json()

    assert report["fill_ratio"] == 1.0
    assert report["execution_count"] == 2
    assert report["avg_execution_price"] is not None
    assert report["first_execution_at"] is not None
    assert report["last_execution_at"] is not None
    assert report["execution_span_seconds"] >= 0.0
