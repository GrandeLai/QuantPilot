"""前端契约回归测试.

覆盖 2026-04 前端增强计划中的关键闭环：
- /api 路由别名在开发环境可用
- 用户策略进入可运行策略目录
- 模拟盘历史记录接口可被前端消费
"""

from pathlib import Path

from fastapi.testclient import TestClient

from quantpilot_common.strategy_persistence import StrategyMeta, StrategyRecord, StrategyStorage


def test_api_aliases_are_available(client: TestClient) -> None:
    """前端统一使用 /api 前缀时，关键 stock 接口应可访问."""
    assert client.get("/api/data/symbols").status_code == 200
    assert client.get("/api/crypto/status").status_code == 200


def test_available_strategies_include_user_strategies(
    client: TestClient,
    monkeypatch,
    tmp_path: Path,
) -> None:
    """可运行策略目录应包含 stock 本地用户策略.

    Stock-assistant 仅返回用户策略；模板策略由 Rust quant-assistant 提供。
    """
    monkeypatch.setenv("QUANTPILOT_STRATEGY_DIR", str(tmp_path))

    storage = StrategyStorage(tmp_path)
    storage.save(
        StrategyRecord(
            meta=StrategyMeta(
                id="user001",
                name="My User Strategy",
                description="user-owned strategy",
                params={"lookback": 21},
            ),
            code=(
                "from quantpilot_common.contracts import BaseStrategy\n"
                "class MyUserStrategy(BaseStrategy):\n"
                "    name = 'My User Strategy'\n"
                "    description = 'user-owned strategy'\n"
                "    default_params = {'lookback': 21}\n"
                "    def on_bar(self, bar, context):\n"
                "        return None\n"
            ),
        )
    )

    response = client.get("/api/portfolio/available-strategies")
    assert response.status_code == 200
    body = response.json()

    strategies = body["strategies"]
    assert any(item["id"] == "user001" and item["source"] == "user" for item in strategies)


def test_paper_order_history_endpoint_returns_frontend_shape(client: TestClient) -> None:
    """图表与模拟盘页面需要可直接消费的成交记录列表."""
    session_id = "frontend-contract-session"

    create_resp = client.post(
        "/api/paper/sessions",
        json={
            "session_id": session_id,
            "symbol": "AAPL",
            "timeframe": "1d",
            "initial_cash": 100000,
        },
    )
    assert create_resp.status_code in (200, 409)

    buy_resp = client.post(
        f"/api/paper/sessions/{session_id}/orders",
        json={"symbol": "AAPL", "side": "buy", "quantity": 10, "price": 100.0},
    )
    assert buy_resp.status_code == 200

    sell_resp = client.post(
        f"/api/paper/sessions/{session_id}/orders",
        json={"symbol": "AAPL", "side": "sell", "quantity": 10, "price": 110.0},
    )
    assert sell_resp.status_code == 200

    history_resp = client.get(f"/api/paper/sessions/{session_id}/orders")
    assert history_resp.status_code == 200
    body = history_resp.json()
    assert body["session_id"] == session_id
    assert len(body["orders"]) >= 1
    assert body["orders"][0]["symbol"] == "AAPL"
