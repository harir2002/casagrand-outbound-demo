"""Integration tests: lead filters → Twilio outbound call (mocked REST)."""

from __future__ import annotations

from datetime import datetime

import pytest

from app.core.config import reset_settings_cache
from app.integrations.twilio import call_registry
from app.integrations.twilio.config import load_twilio_config
from app.integrations.twilio.schemas import OutboundCallRequest
from app.integrations.twilio.service import TwilioCallService
from app.models.session import FlowBucket
from app.services import lead_filter
from app.services.session_store import store


class _FakeTwilioClient:
    def __init__(self, config):
        self.config = config
        self.calls = []

    async def create_call(self, **kwargs):
        self.calls.append(kwargs)
        return {"sid": "CAlead1", "status": "queued", "direction": "outbound-api"}


class _FixedDatetime:
    """Pin lead_filter's clock to 10:00 so call windows are deterministic."""

    @staticmethod
    def now():
        return datetime(2026, 7, 16, 10, 0, 0)


def _twilio_env(monkeypatch):
    monkeypatch.setenv("TWILIO_ENABLED", "true")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACxxxxxxxx")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+15551234567")
    monkeypatch.setenv("TWILIO_PUBLIC_BASE_URL", "https://demo.example.ngrok.app")
    monkeypatch.setenv("TWILIO_VALIDATE_SIGNATURES", "false")
    reset_settings_cache()
    monkeypatch.setattr(lead_filter, "datetime", _FixedDatetime)


# ---------------------------------------------------------------- lead endpoints

def test_get_leads_endpoint(client):
    response = client.get("/leads")
    assert response.status_code == 200
    leads = response.json()
    assert len(leads) == 9
    assert {lead["lead_id"] for lead in leads} >= {"lead-anitha", "lead-priya"}


def test_filter_endpoint_returns_structured_result(client):
    response = client.post(
        "/leads/filter",
        json={"current_hour": 10},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 9
    assert body["passed"] == 4
    assert body["blocked_count"] == 5
    assert body["eligible"][0]["bucket"] in {
        "introduction",
        "education",
        "next_steps",
        "closing_summary",
    }
    blocked_ids = {b["lead"]["lead_id"] for b in body["blocked"]}
    assert "lead-priya" in blocked_ids  # DNC
    priya = next(b for b in body["blocked"] if b["lead"]["lead_id"] == "lead-priya")
    assert any(r["code"] == "dnc_listed" for r in priya["reasons"])


def test_filter_endpoint_project_language(client):
    response = client.post(
        "/leads/filter",
        json={"project_id": "avenuepark", "language": "tanglish", "current_hour": 10},
    )
    body = response.json()
    assert body["passed"] == 1
    assert body["eligible"][0]["lead"]["lead_id"] == "lead-meena"
    assert body["eligible"][0]["bucket"] == "next_steps"


# ---------------------------------------------------------------- filtered lead → Twilio

@pytest.mark.asyncio
async def test_eligible_lead_flows_into_twilio_call(monkeypatch):
    _twilio_env(monkeypatch)
    store.clear()
    call_registry.clear()

    cfg = load_twilio_config()
    fake = _FakeTwilioClient(cfg)
    service = TwilioCallService(config=cfg, client=fake)

    result = await service.start_outbound_call(
        OutboundCallRequest(lead_id="lead-anitha")
    )

    # Twilio dialed the lead's phone with the session-scoped webhook URL
    assert fake.calls[0]["to"] == "+919876543210"
    assert "session_id=" in fake.calls[0]["url"]
    assert "project_id=highcity" in fake.calls[0]["url"]

    # Response preserves lead + bucket metadata
    assert result.to == "+919876543210"
    assert result.project_id == "highcity"
    assert result.language == "en"
    assert result.provider_meta["lead"]["lead_id"] == "lead-anitha"
    assert result.provider_meta["lead"]["bucket"] == "education"

    # Session starts in the bucket mapped from the lead status (interested)
    session = store.get(result.session_id)
    assert session.flow_bucket == FlowBucket.EDUCATION
    assert session.previous_bucket == FlowBucket.INTRODUCTION

    # Registry tracks the lead call like any other outbound call
    entry = call_registry.get_call(result.call_sid)
    assert entry["to"] == "+919876543210"
    store.clear()
    call_registry.clear()


@pytest.mark.asyncio
async def test_converted_lead_starts_in_closing_bucket(monkeypatch):
    _twilio_env(monkeypatch)
    store.clear()

    cfg = load_twilio_config()
    service = TwilioCallService(config=cfg, client=_FakeTwilioClient(cfg))
    result = await service.start_outbound_call(
        OutboundCallRequest(lead_id="lead-suresh")
    )
    assert store.get(result.session_id).flow_bucket == FlowBucket.CLOSING_SUMMARY
    store.clear()


@pytest.mark.asyncio
async def test_blocked_lead_never_reaches_twilio(monkeypatch):
    _twilio_env(monkeypatch)
    cfg = load_twilio_config()
    fake = _FakeTwilioClient(cfg)
    service = TwilioCallService(config=cfg, client=fake)

    with pytest.raises(lead_filter.LeadBlockedError):
        await service.start_outbound_call(OutboundCallRequest(lead_id="lead-priya"))
    assert fake.calls == []


# ---------------------------------------------------------------- route-level blocking

def test_outbound_call_route_blocks_dnc_lead(client, monkeypatch):
    _twilio_env(monkeypatch)
    response = client.post("/twilio/outbound-call", json={"lead_id": "lead-priya"})
    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["blocked"] is True
    assert detail["lead_id"] == "lead-priya"
    assert any(r["code"] == "dnc_listed" for r in detail["reasons"])


def test_outbound_call_route_blocks_no_consent_lead(client, monkeypatch):
    _twilio_env(monkeypatch)
    response = client.post("/twilio/outbound-call", json={"lead_id": "lead-karthik"})
    assert response.status_code == 409
    detail = response.json()["detail"]
    assert any(r["code"] == "no_consent" for r in detail["reasons"])


def test_outbound_call_route_unknown_lead(client, monkeypatch):
    _twilio_env(monkeypatch)
    response = client.post("/twilio/outbound-call", json={"lead_id": "lead-nope"})
    assert response.status_code == 404


def test_outbound_call_requires_to_or_lead(client, monkeypatch):
    _twilio_env(monkeypatch)
    response = client.post("/twilio/outbound-call", json={})
    assert response.status_code == 422
    assert "lead_id" in response.text
