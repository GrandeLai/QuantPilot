"""pytest 公共配置与 fixtures（Phase A 过渡态：仅供量化路由测试）."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """返回隔离存储的 FastAPI 测试客户端（quant routes only after PR 4）."""
    monkeypatch.setenv("QUANTPILOT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("QUANTPILOT_DUCKDB_PATH", str(tmp_path / "quantpilot.duckdb"))
    monkeypatch.setenv("QUANTPILOT_SQLITE_PATH", str(tmp_path / "quantpilot.sqlite"))
    monkeypatch.setenv("QUANTPILOT_STRATEGY_DIR", str(tmp_path / "strategies"))
    monkeypatch.setenv("QUANTPILOT_LOG_DIR", str(tmp_path / "logs"))

    # Lazy import: avoid pulling stock modules that have been moved to apps/stock-assistant
    from quantpilot.main import app

    from quantpilot_common.data import get_storage as _get_storage_fn  # noqa: F401
    from quantpilot_common.data import _storage as _shared_storage  # type: ignore  # noqa: F401
    import quantpilot_common.data as _common_data
    _common_data._storage = None

    client = TestClient(app)
    try:
        yield client
    finally:
        client.close()
        _common_data._storage = None
