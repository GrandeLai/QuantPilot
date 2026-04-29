"""API tests for /advisor/* endpoints (phaseF.assistant-advisor-backend)."""
from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

import quantpilot_stock.api.advisor as advisor_module
from quantpilot_stock.main import app

client = TestClient(app)


# ---------- helpers ----------------------------------------------------------


def _neutral_signal() -> dict[str, Any]:
    return {"signal": "neutral", "z_score": 0.0, "percentile": 50.0, "funding_rate": 0.0001}


def _contrarian_long_signal() -> dict[str, Any]:
    return {"signal": "contrarian_long", "z_score": -2.5, "percentile": 3.0, "funding_rate": -0.0002}


def _contrarian_short_signal() -> dict[str, Any]:
    return {"signal": "contrarian_short", "z_score": 2.8, "percentile": 97.0, "funding_rate": 0.0008}


def _low_funding_signal() -> dict[str, Any]:
    return {"signal": "neutral", "z_score": -0.8, "percentile": 20.0, "funding_rate": 0.00005}


def _high_funding_signal() -> dict[str, Any]:
    return {"signal": "neutral", "z_score": 0.9, "percentile": 75.0, "funding_rate": 0.0003}


# ---------- /advisor/overview ------------------------------------------------


class TestAdvisorOverview:
    def test_returns_200_and_schema(self) -> None:
        r = client.get("/advisor/overview")
        assert r.status_code == 200
        body = r.json()
        assert "net_worth" in body
        assert "cash_ratio" in body
        assert "positions" in body
        assert "generated_at" in body
        assert isinstance(body["net_worth"], float | int)
        assert 0.0 <= body["cash_ratio"] <= 1.0

    def test_positions_is_list(self) -> None:
        r = client.get("/advisor/overview")
        assert isinstance(r.json()["positions"], list)

    def test_api_alias_works(self) -> None:
        r = client.get("/api/advisor/overview")
        assert r.status_code == 200


# ---------- /advisor/crypto/opportunities ------------------------------------


class TestCryptoOpportunities:
    def test_neutral_signal_no_items(self, monkeypatch: pytest.MonkeyPatch) -> None:
        sig = _neutral_signal()

        async def fake_signal(asset: str) -> dict[str, Any]:
            return sig

        monkeypatch.setattr(advisor_module, "_get_funding_signal", fake_signal)
        r = client.get("/advisor/crypto/opportunities?symbol=BTC-USDT")
        assert r.status_code == 200
        assert r.json()["items"] == []

    def test_contrarian_long_produces_item(self, monkeypatch: pytest.MonkeyPatch) -> None:
        sig = _contrarian_long_signal()

        async def fake_signal(asset: str) -> dict[str, Any]:
            return sig

        monkeypatch.setattr(advisor_module, "_get_funding_signal", fake_signal)
        r = client.get("/advisor/crypto/opportunities?symbol=BTC-USDT")
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        item = items[0]
        assert item["type"] == "long_opportunity"
        assert item["subject"] == "BTC-USDT"
        assert 0.5 < item["confidence"] <= 0.92
        assert len(item["evidence"]) >= 1
        assert len(item["risk_notes"]) >= 1

    def test_low_funding_neutral_produces_basis_item(self, monkeypatch: pytest.MonkeyPatch) -> None:
        sig = _low_funding_signal()

        async def fake_signal(asset: str) -> dict[str, Any]:
            return sig

        monkeypatch.setattr(advisor_module, "_get_funding_signal", fake_signal)
        r = client.get("/advisor/crypto/opportunities?symbol=ETH-USDT")
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        assert items[0]["type"] == "basis_opportunity"
        assert items[0]["subject"] == "ETH-USDT"

    def test_contrarian_short_no_opportunity(self, monkeypatch: pytest.MonkeyPatch) -> None:
        sig = _contrarian_short_signal()

        async def fake_signal(asset: str) -> dict[str, Any]:
            return sig

        monkeypatch.setattr(advisor_module, "_get_funding_signal", fake_signal)
        r = client.get("/advisor/crypto/opportunities?symbol=BTC-USDT")
        assert r.status_code == 200
        assert r.json()["items"] == []

    def test_api_alias_works(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_signal(asset: str) -> dict[str, Any]:
            return _neutral_signal()

        monkeypatch.setattr(advisor_module, "_get_funding_signal", fake_signal)
        r = client.get("/api/advisor/crypto/opportunities?symbol=BTC-USDT")
        assert r.status_code == 200

    def test_default_symbol_is_btc(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: list[str] = []

        async def fake_signal(asset: str) -> dict[str, Any]:
            captured.append(asset)
            return _neutral_signal()

        monkeypatch.setattr(advisor_module, "_get_funding_signal", fake_signal)
        client.get("/advisor/crypto/opportunities")
        assert captured == ["BTC"]


# ---------- /advisor/crypto/risks --------------------------------------------


class TestCryptoRisks:
    def test_neutral_signal_no_items(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_signal(asset: str) -> dict[str, Any]:
            return _neutral_signal()

        monkeypatch.setattr(advisor_module, "_get_funding_signal", fake_signal)
        r = client.get("/advisor/crypto/risks?symbol=BTC-USDT")
        assert r.status_code == 200
        assert r.json()["items"] == []

    def test_contrarian_short_produces_risk(self, monkeypatch: pytest.MonkeyPatch) -> None:
        sig = _contrarian_short_signal()

        async def fake_signal(asset: str) -> dict[str, Any]:
            return sig

        monkeypatch.setattr(advisor_module, "_get_funding_signal", fake_signal)
        r = client.get("/advisor/crypto/risks?symbol=BTC-USDT")
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        item = items[0]
        assert item["type"] == "crowded_long_risk"
        assert item["subject"] == "BTC-USDT"
        assert 0.5 < item["confidence"] <= 0.92
        assert len(item["evidence"]) >= 1
        # risk_notes should mention annual cost
        assert any("%" in note for note in item["risk_notes"])

    def test_high_funding_neutral_produces_elevated_risk(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_signal(asset: str) -> dict[str, Any]:
            return _high_funding_signal()

        monkeypatch.setattr(advisor_module, "_get_funding_signal", fake_signal)
        r = client.get("/advisor/crypto/risks?symbol=ETH-USDT")
        assert r.status_code == 200
        items = r.json()["items"]
        assert len(items) == 1
        assert items[0]["type"] == "elevated_funding_risk"

    def test_contrarian_long_no_risk(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_signal(asset: str) -> dict[str, Any]:
            return _contrarian_long_signal()

        monkeypatch.setattr(advisor_module, "_get_funding_signal", fake_signal)
        r = client.get("/advisor/crypto/risks?symbol=BTC-USDT")
        assert r.status_code == 200
        assert r.json()["items"] == []

    def test_api_alias_works(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_signal(asset: str) -> dict[str, Any]:
            return _neutral_signal()

        monkeypatch.setattr(advisor_module, "_get_funding_signal", fake_signal)
        r = client.get("/api/advisor/crypto/risks?symbol=BTC-USDT")
        assert r.status_code == 200
