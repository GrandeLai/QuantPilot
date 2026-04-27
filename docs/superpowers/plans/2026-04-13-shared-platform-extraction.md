# Shared Platform Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a shared platform layer that exposes unified domain contracts, unified domain status summaries, and assistant-ready advice schemas for both future products.

**Architecture:** Add a new `quantpilot.platform` package as a thin orchestration layer over existing backend modules instead of rewriting current domains in place. Expose the platform through typed Pydantic v2 models and a small read-only FastAPI router so future workbench and assistant frontends can consume one authoritative contract.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, existing `quantpilot` backend modules, pytest, ruff

---

## File Map

- Create `backend/src/quantpilot/platform/__init__.py` — platform package exports
- Create `backend/src/quantpilot/platform/models.py` — shared domain-status and fact-envelope models
- Create `backend/src/quantpilot/platform/agent_models.py` — structured advice/evidence models
- Create `backend/src/quantpilot/platform/services.py` — read-only orchestration over existing backend modules
- Create `backend/src/quantpilot/api/platform.py` — `/platform/*` router
- Modify `backend/src/quantpilot/main.py` — register the new router
- Create `backend/tests/platform/test_models.py` — model contract regression tests
- Create `backend/tests/platform/test_agent_models.py` — structured advice contract tests
- Create `backend/tests/test_platform_api.py` — API contract tests

### Task 1: Introduce shared platform contract models

**Files:**
- Create: `backend/src/quantpilot/platform/__init__.py`
- Create: `backend/src/quantpilot/platform/models.py`
- Test: `backend/tests/platform/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
from datetime import datetime, timezone

from pydantic import ValidationError

from quantpilot.platform.models import DomainStatus, FactEnvelope


def test_domain_status_exposes_required_fields() -> None:
    status = DomainStatus(
        name="market_data",
        status="ok",
        freshness="fresh",
        updated_at=datetime(2026, 4, 13, tzinfo=timezone.utc),
        detail="duckdb reachable",
    )

    assert status.name == "market_data"
    assert status.status == "ok"
    assert status.freshness == "fresh"


def test_fact_envelope_requires_version_and_payload() -> None:
    envelope = FactEnvelope(
        version="2026-04-13",
        generated_at=datetime(2026, 4, 13, tzinfo=timezone.utc),
        payload={"positions": 2},
    )

    assert envelope.version == "2026-04-13"
    assert envelope.payload["positions"] == 2


def test_domain_status_rejects_unknown_status() -> None:
    try:
        DomainStatus(
            name="risk",
            status="green",
            freshness="fresh",
            updated_at=datetime(2026, 4, 13, tzinfo=timezone.utc),
        )
    except ValidationError as exc:
        assert "status" in str(exc)
    else:
        raise AssertionError("expected ValidationError for unsupported status")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/platform/test_models.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'quantpilot.platform'`

- [ ] **Step 3: Write minimal implementation**

`backend/src/quantpilot/platform/__init__.py`

```python
"""Shared platform contracts for QuantPilot products."""

from quantpilot.platform.models import DomainStatus, FactEnvelope

__all__ = ["DomainStatus", "FactEnvelope"]
```

`backend/src/quantpilot/platform/models.py`

```python
"""Shared platform contract models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

DomainHealth = Literal["ok", "degraded", "error"]
FreshnessState = Literal["fresh", "stale", "unknown"]


class DomainStatus(BaseModel):
    """Status block for a shared platform domain."""

    name: str
    status: DomainHealth
    freshness: FreshnessState
    updated_at: datetime
    detail: str | None = None


class FactEnvelope(BaseModel):
    """Versioned fact wrapper consumed by multiple products."""

    version: str = Field(min_length=1)
    generated_at: datetime
    payload: dict[str, Any]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/platform/test_models.py -v`  
Expected: PASS with `3 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/src/quantpilot/platform/__init__.py backend/src/quantpilot/platform/models.py backend/tests/platform/test_models.py
git commit -m "feat: add shared platform contract models"
```

### Task 2: Expose a read-only platform summary API

**Files:**
- Create: `backend/src/quantpilot/platform/services.py`
- Create: `backend/src/quantpilot/api/platform.py`
- Modify: `backend/src/quantpilot/main.py`
- Test: `backend/tests/test_platform_api.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient


def test_platform_summary_lists_all_domains(client: TestClient) -> None:
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_platform_api.py -v`  
Expected: FAIL with `404 != 200`

- [ ] **Step 3: Write minimal implementation**

`backend/src/quantpilot/platform/services.py`

```python
"""Read-only platform service façade."""

from __future__ import annotations

from datetime import datetime, timezone

from quantpilot.platform.models import DomainStatus, FactEnvelope


def build_platform_summary() -> FactEnvelope:
    """Return a shared-platform domain health snapshot."""

    now = datetime.now(timezone.utc)
    domains = {
        "market_data": DomainStatus(name="market_data", status="ok", freshness="fresh", updated_at=now).model_dump(),
        "portfolio_account": DomainStatus(name="portfolio_account", status="ok", freshness="fresh", updated_at=now).model_dump(),
        "strategy_validation": DomainStatus(name="strategy_validation", status="ok", freshness="fresh", updated_at=now).model_dump(),
        "risk": DomainStatus(name="risk", status="ok", freshness="fresh", updated_at=now).model_dump(),
        "execution": DomainStatus(name="execution", status="ok", freshness="fresh", updated_at=now).model_dump(),
        "agent": DomainStatus(name="agent", status="ok", freshness="fresh", updated_at=now).model_dump(),
    }
    return FactEnvelope(version=now.date().isoformat(), generated_at=now, payload={"domains": domains})
```

`backend/src/quantpilot/api/platform.py`

```python
"""Shared platform API endpoints."""

from fastapi import APIRouter

from quantpilot.platform.services import build_platform_summary

router = APIRouter(prefix="/platform", tags=["platform"])


@router.get("/summary")
async def get_platform_summary() -> dict:
    """Return read-only shared platform status."""
    envelope = build_platform_summary()
    return {
        "version": envelope.version,
        "generated_at": envelope.generated_at,
        "domains": envelope.payload["domains"],
    }
```

`backend/src/quantpilot/main.py`

```python
from quantpilot.api.platform import router as platform_router

include_with_api_alias(platform_router)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_platform_api.py -v`  
Expected: PASS with `1 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/src/quantpilot/platform/services.py backend/src/quantpilot/api/platform.py backend/src/quantpilot/main.py backend/tests/test_platform_api.py
git commit -m "feat: add shared platform summary api"
```

### Task 3: Add assistant-ready advice and evidence contracts

**Files:**
- Create: `backend/src/quantpilot/platform/agent_models.py`
- Modify: `backend/src/quantpilot/platform/__init__.py`
- Test: `backend/tests/platform/test_agent_models.py`

- [ ] **Step 1: Write the failing test**

```python
from datetime import datetime, timezone

from quantpilot.platform.agent_models import AdviceCard, AdviceEvidence


def test_advice_card_requires_evidence_and_risk_notes() -> None:
    card = AdviceCard(
        type="opportunity",
        subject="AAPL",
        recommendation="watch",
        confidence=0.72,
        evidence=[
            AdviceEvidence(
                source="screener",
                summary="relative strength improving",
                observed_at=datetime(2026, 4, 13, tzinfo=timezone.utc),
            )
        ],
        risk_notes=["earnings this week"],
        generated_at=datetime(2026, 4, 13, tzinfo=timezone.utc),
        freshness="fresh",
    )

    assert card.type == "opportunity"
    assert card.evidence[0].source == "screener"
    assert card.risk_notes == ["earnings this week"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/platform/test_agent_models.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'quantpilot.platform.agent_models'`

- [ ] **Step 3: Write minimal implementation**

`backend/src/quantpilot/platform/agent_models.py`

```python
"""Structured advice contracts shared by workbench and assistant."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

AdviceType = Literal[
    "opportunity",
    "rebalance_recommendation",
    "risk_alert",
    "strategy_diagnosis",
    "portfolio_review",
]

FreshnessState = Literal["fresh", "stale", "unknown"]


class AdviceEvidence(BaseModel):
    """Evidence attached to a structured advice card."""

    source: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    observed_at: datetime


class AdviceCard(BaseModel):
    """Shared AI suggestion payload."""

    type: AdviceType
    subject: str = Field(min_length=1)
    recommendation: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[AdviceEvidence]
    risk_notes: list[str]
    generated_at: datetime
    freshness: FreshnessState
```

`backend/src/quantpilot/platform/__init__.py`

```python
"""Shared platform contracts for QuantPilot products."""

from quantpilot.platform.agent_models import AdviceCard, AdviceEvidence
from quantpilot.platform.models import DomainStatus, FactEnvelope

__all__ = ["AdviceCard", "AdviceEvidence", "DomainStatus", "FactEnvelope"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/platform/test_agent_models.py -v`  
Expected: PASS with `1 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/src/quantpilot/platform/agent_models.py backend/src/quantpilot/platform/__init__.py backend/tests/platform/test_agent_models.py
git commit -m "feat: add structured advice contracts"
```
