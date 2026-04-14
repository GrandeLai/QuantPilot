"""交易 API 回归测试 — Longbridge-first / mock-fallback."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_trading_provider(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """强制交易层使用 mock provider，便于本地闭环验证."""
    monkeypatch.setenv("QUANTPILOT_TRADING_PROVIDER", "mock")

    from quantpilot.broker.provider import get_trading_provider

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


def test_order_rejected_when_max_order_value_exceeded(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """统一 trading 主线应在提交前执行最大单笔金额风控."""
    monkeypatch.setenv("QUANTPILOT_TRADING_PROVIDER", "mock")
    monkeypatch.setenv("QUANTPILOT_TRADING_RISK_MAX_ORDER_VALUE", "1000")

    from quantpilot.broker.provider import get_trading_provider

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

    from quantpilot.broker.mock import MockTradingProvider
    from quantpilot.broker.provider import get_trading_provider

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
