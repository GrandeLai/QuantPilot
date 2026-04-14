"""pytest 公共配置与 fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from quantpilot.main import app


@pytest.fixture
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """返回隔离存储的 FastAPI 测试客户端."""
    monkeypatch.setenv("QUANTPILOT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("QUANTPILOT_DUCKDB_PATH", str(tmp_path / "quantpilot.duckdb"))
    monkeypatch.setenv("QUANTPILOT_SQLITE_PATH", str(tmp_path / "quantpilot.sqlite"))
    monkeypatch.setenv("QUANTPILOT_STRATEGY_DIR", str(tmp_path / "strategies"))
    monkeypatch.setenv("QUANTPILOT_LOG_DIR", str(tmp_path / "logs"))

    from quantpilot.api import data as data_api
    from quantpilot.broker.provider import get_trading_provider
    from quantpilot.trading.oms import get_order_event_store

    data_api._storage = None
    get_trading_provider.cache_clear()
    get_order_event_store().reset()
    client = TestClient(app)
    try:
        yield client
    finally:
        client.close()
        data_api._storage = None
        get_trading_provider.cache_clear()
        get_order_event_store().reset()
