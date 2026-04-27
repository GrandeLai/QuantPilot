"""FastAPI 主应用接口测试 — T-0.1 验收测试."""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """验证健康检查端点返回 200 且 status=ok."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_root(client: TestClient) -> None:
    """验证根路径返回欢迎信息."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_openapi_schema(client: TestClient) -> None:
    """验证 OpenAPI schema 可正常访问."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "QuantPilot (Quant Assistant Py)"
