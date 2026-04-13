"""Regression tests for investment assistant API endpoints."""

from fastapi.testclient import TestClient


def test_advisor_overview_returns_structured_snapshot(client: TestClient) -> None:
    """Overview endpoint should return the expected structured snapshot."""
    response = client.get("/api/advisor/overview")
    assert response.status_code == 200

    body = response.json()
    assert {"net_worth", "cash_ratio", "positions", "generated_at"} <= body.keys()


def test_advisor_opportunities_return_advice_cards(client: TestClient) -> None:
    """Opportunities endpoint should return assistant-ready advice cards."""
    response = client.get("/api/advisor/opportunities")
    assert response.status_code == 200

    body = response.json()
    assert isinstance(body["items"], list)
    if body["items"]:
        first = body["items"][0]
        assert {
            "type",
            "subject",
            "recommendation",
            "confidence",
            "evidence",
        } <= first.keys()
