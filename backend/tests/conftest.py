"""pytest 公共配置与 fixtures."""

import pytest
from fastapi.testclient import TestClient

from quantpilot.main import app


@pytest.fixture
def client() -> TestClient:
    """返回 FastAPI 测试客户端."""
    return TestClient(app)
