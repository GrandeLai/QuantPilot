"""Regression tests for investment assistant API endpoints."""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from quantpilot.api.advisor import AdvisorOpportunitiesResponse, AdvisorOverviewResponse
from quantpilot.data.models import OHLCVBar
from quantpilot.data.storage import MarketDataStorage


def _make_bar(
    *,
    symbol: str,
    timeframe: str,
    timestamp: datetime,
    close: float,
    volume: float = 1_000.0,
) -> OHLCVBar:
    return OHLCVBar(
        symbol=symbol,
        timeframe=timeframe,
        timestamp=timestamp,
        open=close * 0.99,
        high=close * 1.01,
        low=close * 0.98,
        close=close,
        volume=volume,
    )


def _seed_crypto(storage: MarketDataStorage, symbol: str = "BTC-USDT") -> None:
    base = datetime(2025, 1, 1, tzinfo=UTC)
    bars: list[OHLCVBar] = []
    for i in range(240):
        ts = base + timedelta(minutes=15 * i)
        bars.append(_make_bar(symbol=symbol, timeframe="15m", timestamp=ts, close=100_000 + i * 10, volume=1_000 + i))
    for i in range(60):
        ts = base + timedelta(hours=i)
        bars.append(_make_bar(symbol=symbol, timeframe="1h", timestamp=ts, close=99_500 + i * 25, volume=4_000 + i))
    for i in range(30):
        ts = base + timedelta(hours=4 * i)
        bars.append(_make_bar(symbol=symbol, timeframe="4h", timestamp=ts, close=99_000 + i * 50, volume=16_000 + i))
    for i in range(20):
        ts = base + timedelta(days=i)
        bars.append(_make_bar(symbol=symbol, timeframe="1d", timestamp=ts, close=98_000 + i * 100, volume=64_000 + i))
    for i in range(6):
        ts = base + timedelta(days=7 * i)
        bars.append(_make_bar(symbol=symbol, timeframe="1w", timestamp=ts, close=97_000 + i * 200, volume=256_000 + i))
    storage.upsert_bars(bars)


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


def test_advisor_crypto_opportunities_return_crypto_cards(client: TestClient, monkeypatch) -> None:
    """Crypto opportunities should be derived from the crypto research stack."""
    from quantpilot.api import data as data_api

    storage = MarketDataStorage(db_path=":memory:")
    _seed_crypto(storage)
    monkeypatch.setattr(data_api, "_storage", storage)

    response = client.get("/api/advisor/crypto/opportunities?symbol=BTC-USDT")
    assert response.status_code == 200

    body = response.json()
    opportunities = AdvisorOpportunitiesResponse.model_validate(body)
    assert opportunities.items
    first = opportunities.items[0]
    assert first.subject == "BTC-USDT"
    assert first.type == "opportunity"
    assert first.evidence
    assert any("市场状态" in item.summary for item in first.evidence)
    assert any("vwap_ema_trend" in note for note in first.risk_notes)


def test_advisor_crypto_risks_return_risk_alerts(client: TestClient, monkeypatch) -> None:
    """Crypto risks should expose structured risk-alert cards."""
    from quantpilot.api import data as data_api

    storage = MarketDataStorage(db_path=":memory:")
    _seed_crypto(storage)
    monkeypatch.setattr(data_api, "_storage", storage)

    response = client.get("/api/advisor/crypto/risks?symbol=BTC-USDT")
    assert response.status_code == 200

    body = response.json()
    risks = AdvisorOpportunitiesResponse.model_validate(body)
    assert risks.items
    assert all(item.type == "risk_alert" for item in risks.items)
    assert any("市场状态" in item.summary for item in risks.items[0].evidence)
    assert any("推荐策略" in note for note in risks.items[0].risk_notes)
