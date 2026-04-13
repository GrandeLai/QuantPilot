"""Regression tests for investment assistant API endpoints."""

from fastapi.testclient import TestClient

from quantpilot.api.advisor import AdvisorOpportunitiesResponse, AdvisorOverviewResponse


def test_advisor_overview_returns_structured_snapshot(client: TestClient) -> None:
    """Overview endpoint should return the expected structured snapshot."""
    response = client.get("/api/advisor/overview")
    assert response.status_code == 200

    body = response.json()
    overview = AdvisorOverviewResponse.model_validate(body)
    assert {"net_worth", "cash_ratio", "positions", "generated_at"} <= body.keys()
    assert overview.net_worth == 100000.0
    assert overview.cash_ratio == 0.35


def test_advisor_opportunities_return_advice_cards(client: TestClient) -> None:
    """Opportunities endpoint should return assistant-ready advice cards."""
    response = client.get("/api/advisor/opportunities")
    assert response.status_code == 200

    body = response.json()
    opportunities = AdvisorOpportunitiesResponse.model_validate(body)
    assert isinstance(body["items"], list)
    if opportunities.items:
        first = opportunities.items[0]
        assert first.type == "opportunity"
        assert first.subject == "AAPL"
        assert first.freshness == "fresh"
        assert first.risk_notes
        assert first.evidence
