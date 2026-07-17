"""Integration tests: campaign endpoints + real dial path (mocked Twilio REST).

Covers filtered lead selection, the sequential dial run through the real
TwilioCallService (safety gate + session bucket transitions), blocked lead
handling, status-callback-driven progress, and summary generation.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from app.core.config import reset_settings_cache
from app.integrations.twilio import call_registry
from app.integrations.twilio import service as twilio_service
from app.models.campaign import CampaignStatus
from app.models.lead import LeadFilterRequest
from app.models.session import FlowBucket
from app.services import campaign_service, lead_filter
from app.services.session_store import store


class _FixedDatetime:
    @staticmethod
    def now():
        return datetime(2026, 7, 16, 10, 0, 0)


class _FakeRestClient:
    """Drop-in for TwilioRestClient — records dials, returns queued calls."""

    counter = 0
    created: list[dict] = []

    def __init__(self, config):
        self.config = config

    async def create_call(self, **kwargs):
        _FakeRestClient.counter += 1
        payload = {**kwargs, "sid": f"CAcamp{_FakeRestClient.counter}"}
        _FakeRestClient.created.append(payload)
        return {
            "sid": payload["sid"],
            "status": "queued",
            "direction": "outbound-api",
        }


@pytest.fixture(autouse=True)
def _campaign_env(monkeypatch):
    monkeypatch.setenv("TWILIO_ENABLED", "true")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACxxxxxxxx")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+15551234567")
    monkeypatch.setenv("TWILIO_PUBLIC_BASE_URL", "https://demo.example.ngrok.app")
    monkeypatch.setenv("TWILIO_VALIDATE_SIGNATURES", "false")
    reset_settings_cache()
    monkeypatch.setattr(lead_filter, "datetime", _FixedDatetime)
    monkeypatch.setattr(twilio_service, "TwilioRestClient", _FakeRestClient)
    _FakeRestClient.counter = 0
    _FakeRestClient.created = []
    campaign_service.clear_campaigns()
    call_registry.clear()
    store.clear()
    yield
    campaign_service.clear_campaigns()
    call_registry.clear()
    store.clear()


def test_create_campaign_endpoint_filtered_selection(client):
    response = client.post(
        "/campaigns",
        json={"filters": {"project_id": "highcity", "current_hour": 10}},
    )
    assert response.status_code == 200
    body = response.json()
    # Snapshot keeps all leads; non-matching ones are blocked with reasons
    assert body["summary"]["total"] == 9
    assert body["summary"]["eligible"] == 2  # anitha + rajesh (highcity, callable)
    assert body["summary"]["blocked"] == 7
    states = {l["lead_id"]: l["state"] for l in body["campaign"]["leads"]}
    assert states["lead-anitha"] == "pending"
    assert states["lead-priya"] == "blocked"


@pytest.mark.asyncio
async def test_campaign_run_dials_through_real_service_with_buckets():
    """Full dial sequence through TwilioCallService: gate, sessions, buckets."""
    campaign = campaign_service.create_campaign(LeadFilterRequest(current_hour=10))
    done = await campaign_service.run_campaign(
        campaign.campaign_id, wait_for_terminal=False
    )
    assert done.status == CampaignStatus.COMPLETED

    dialed = {l.lead_id: l for l in done.leads if l.call_sid}
    assert set(dialed) == {"lead-anitha", "lead-rajesh", "lead-meena", "lead-suresh"}

    # Twilio REST was called once per eligible lead, never for blocked ones
    assert len(_FakeRestClient.created) == 4
    dialed_numbers = {c["to"] for c in _FakeRestClient.created}
    assert "+919833221100" not in dialed_numbers  # priya (DNC) never dialed

    # Bucket transitions: each session starts in the lead-status bucket
    expected_buckets = {
        "lead-anitha": FlowBucket.EDUCATION,
        "lead-rajesh": FlowBucket.INTRODUCTION,
        "lead-meena": FlowBucket.NEXT_STEPS,
        "lead-suresh": FlowBucket.CLOSING_SUMMARY,
    }
    for lead_id, bucket in expected_buckets.items():
        session = store.get(dialed[lead_id].session_id)
        assert session.flow_bucket == bucket, lead_id

    # Calls are tracked in the registry like manual dials
    for result in dialed.values():
        assert call_registry.get_call(result.call_sid) is not None


def test_campaign_progress_via_status_callbacks(client):
    """Status callbacks flow into campaign lead states through GET refresh."""
    created = client.post(
        "/campaigns",
        json={"filters": {"project_id": "highcity", "current_hour": 10}},
    ).json()
    campaign_id = created["campaign"]["campaign_id"]

    started = client.post(
        f"/campaigns/{campaign_id}/start",
        json={"wait_for_terminal": False},
    )
    assert started.status_code == 200

    # Let the background task finish dialing (each GET advances the loop)
    body = None
    for _ in range(50):
        body = client.get(f"/campaigns/{campaign_id}").json()
        if body["summary"]["done"]:
            break
    assert body["summary"]["done"] is True

    dialed = [l for l in body["campaign"]["leads"] if l["call_sid"]]
    assert len(dialed) == 2
    assert all(l["state"] == "dialing" for l in dialed)

    # Twilio reports the first call answered, then completed
    sid = dialed[0]["call_sid"]
    client.post("/twilio/status-callback", data={"CallSid": sid, "CallStatus": "in-progress"})
    refreshed = client.get(f"/campaigns/{campaign_id}").json()
    states = {l["lead_id"]: l["state"] for l in refreshed["campaign"]["leads"]}
    assert states[dialed[0]["lead_id"]] == "connected"

    client.post(
        "/twilio/status-callback",
        data={"CallSid": sid, "CallStatus": "completed", "CallDuration": "42"},
    )
    final = client.get(f"/campaigns/{campaign_id}").json()
    lead = next(l for l in final["campaign"]["leads"] if l["call_sid"] == sid)
    assert lead["state"] == "completed"
    assert lead["duration"] == "42"
    assert final["summary"]["states"]["completed"] == 1


def test_start_twice_conflicts_and_cancel(client):
    created = client.post(
        "/campaigns",
        json={"filters": {"project_id": "highcity", "current_hour": 10}},
    ).json()
    campaign_id = created["campaign"]["campaign_id"]

    client.post(f"/campaigns/{campaign_id}/start", json={"wait_for_terminal": False})
    for _ in range(50):
        if client.get(f"/campaigns/{campaign_id}").json()["summary"]["done"]:
            break
    again = client.post(f"/campaigns/{campaign_id}/start", json={})
    assert again.status_code == 409

    fresh = client.post("/campaigns", json={"filters": {"current_hour": 10}}).json()
    cancelled = client.post(f"/campaigns/{fresh['campaign']['campaign_id']}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["campaign"]["status"] == "cancelled"
    assert cancelled.json()["summary"]["done"] is True


def test_unknown_campaign_returns_404(client):
    assert client.get("/campaigns/cmp-nope").status_code == 404
    assert client.post("/campaigns/cmp-nope/start", json={}).status_code == 404
    assert client.post("/campaigns/cmp-nope/cancel").status_code == 404
