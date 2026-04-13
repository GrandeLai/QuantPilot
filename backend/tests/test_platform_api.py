"""Shared platform API regression tests."""

from fastapi.testclient import TestClient


def test_platform_summary_lists_all_domains(client: TestClient) -> None:
    """Platform summary should expose all shared product domains."""
    response = client.get("/api/platform/summary")
    assert response.status_code == 200

    body = response.json()
    assert body["version"]
    assert set(body["domains"].keys()) == {
        "market_data",
        "portfolio_account",
        "strategy_validation",
        "risk",
        "execution",
        "agent",
    }
    assert body["domains"]["market_data"]["status"] in {"ok", "degraded", "error"}
