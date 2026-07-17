"""Outbound call request building / service tests (mocked Twilio REST)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import reset_settings_cache
from app.integrations.twilio import call_registry
from app.integrations.twilio.config import load_twilio_config
from app.integrations.twilio.schemas import OutboundCallRequest, normalize_e164
from app.integrations.twilio.service import (
    TwilioCallService,
    build_outbound_call_body_for_tests,
)
from app.services.session_store import store


def test_normalize_e164_valid_and_invalid():
    assert normalize_e164("+91 98765-43210") == "+919876543210"
    assert normalize_e164("+1 (555) 123.4567") == "+15551234567"
    assert normalize_e164("9876543210") is None  # missing +
    assert normalize_e164("+0123456789") is None  # leading 0
    assert normalize_e164("") is None
    assert normalize_e164("+91") is None  # too short


def test_outbound_request_normalizes_number():
    req = OutboundCallRequest(to="+91 98765 43210")
    assert req.to == "+919876543210"


def test_outbound_request_rejects_invalid_number():
    with pytest.raises(ValidationError) as exc_info:
        OutboundCallRequest(to="98765")
    assert "E.164" in str(exc_info.value)


def test_outbound_call_body_url_mode():
    body = build_outbound_call_body_for_tests(
        to="+919999999999",
        from_number="+15551234567",
        url="https://demo.example/twilio/voice-webhook?session_id=abc",
    )
    assert body["To"] == "+919999999999"
    assert body["From"] == "+15551234567"
    assert body["Url"].startswith("https://")
    assert body["Method"] == "POST"
    assert "Twiml" not in body


def test_outbound_call_body_inline_twiml():
    body = build_outbound_call_body_for_tests(
        to="+919999999999",
        from_number="+15551234567",
        twiml="<Response><Say>hi</Say></Response>",
    )
    assert body["Twiml"].startswith("<Response>")
    assert "Url" not in body


class _FakeTwilioClient:
    def __init__(self, config):
        self.config = config
        self.calls = []

    async def create_call(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "sid": "CAtest123",
            "status": "queued",
            "direction": "outbound-api",
        }


@pytest.mark.asyncio
async def test_start_outbound_call_creates_session(monkeypatch):
    monkeypatch.setenv("TWILIO_ENABLED", "true")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACxxxxxxxx")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+15551234567")
    monkeypatch.setenv("TWILIO_PUBLIC_BASE_URL", "https://demo.example.ngrok.app")
    reset_settings_cache()
    store.clear()

    cfg = load_twilio_config()
    fake = _FakeTwilioClient(cfg)
    service = TwilioCallService(config=cfg, client=fake)
    result = await service.start_outbound_call(
        OutboundCallRequest(to="+919888877777", project_id="highcity")
    )
    assert result.call_sid == "CAtest123"
    assert result.to == "+919888877777"
    assert result.from_number == "+15551234567"
    assert result.session_id
    assert result.transport == "twilio_voice"
    assert result.media_stream == "websocket"
    assert fake.calls and fake.calls[0]["url"]
    assert "session_id=" in fake.calls[0]["url"]
    assert result.provider_meta["timings"]["initiate_ms"] is not None
    store.clear()


@pytest.mark.asyncio
async def test_start_outbound_call_stores_customer_name(monkeypatch):
    """Name + number flow: the name lands in session CRM memory + metadata."""
    monkeypatch.setenv("TWILIO_ENABLED", "true")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACxxxxxxxx")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+15551234567")
    monkeypatch.setenv("TWILIO_PUBLIC_BASE_URL", "https://demo.example.ngrok.app")
    reset_settings_cache()
    store.clear()

    cfg = load_twilio_config()
    fake = _FakeTwilioClient(cfg)
    service = TwilioCallService(config=cfg, client=fake)
    result = await service.start_outbound_call(
        OutboundCallRequest(to="+91 98888 77777", customer_name="  Anitha Raman  ")
    )
    # Backend received both fields: number normalized, name trimmed
    assert fake.calls[0]["to"] == "+919888877777"
    assert result.provider_meta["customer_name"] == "Anitha Raman"
    session = store.get(result.session_id)
    assert session.memory.caller_name == "Anitha Raman"
    # No project forced: the session starts on the default project
    assert session.project_id
    store.clear()


def test_outbound_request_accepts_blank_name_as_none():
    req = OutboundCallRequest(to="+919888877777", customer_name="   ")
    assert req.customer_name is None


@pytest.mark.asyncio
async def test_start_outbound_call_records_in_registry(monkeypatch):
    monkeypatch.setenv("TWILIO_ENABLED", "true")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACxxxxxxxx")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+15551234567")
    monkeypatch.setenv("TWILIO_PUBLIC_BASE_URL", "https://demo.example.ngrok.app")
    reset_settings_cache()
    store.clear()
    call_registry.clear()

    cfg = load_twilio_config()
    service = TwilioCallService(config=cfg, client=_FakeTwilioClient(cfg))
    result = await service.start_outbound_call(OutboundCallRequest(to="+919888877777"))

    entry = call_registry.get_call(result.call_sid)
    assert entry is not None
    assert entry["to"] == "+919888877777"
    assert entry["session_id"] == result.session_id
    assert entry["status"] == "queued"
    store.clear()
    call_registry.clear()


@pytest.mark.asyncio
async def test_outbound_call_route_requires_twilio(client, monkeypatch):
    monkeypatch.setenv("TWILIO_ENABLED", "false")
    reset_settings_cache()
    response = client.post(
        "/twilio/outbound-call",
        json={"to": "+919999999999"},
    )
    assert response.status_code == 503


def test_outbound_call_route_rejects_bad_number(client, monkeypatch):
    monkeypatch.setenv("TWILIO_ENABLED", "true")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACxxxxxxxx")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+15551234567")
    monkeypatch.setenv("TWILIO_PUBLIC_BASE_URL", "https://demo.example.ngrok.app")
    reset_settings_cache()
    response = client.post(
        "/twilio/outbound-call",
        json={"to": "not-a-number"},
    )
    assert response.status_code == 422
    assert "E.164" in response.text


def test_call_status_endpoint(client):
    call_registry.clear()
    missing = client.get("/twilio/call-status", params={"call_sid": "CAmissing"})
    assert missing.status_code == 404

    call_registry.record_call(
        "CAflow1",
        to="+919888877777",
        from_number="+15551234567",
        session_id="sess-1",
        status="queued",
    )
    call_registry.update_status("CAflow1", "in-progress")
    live = client.get("/twilio/call-status", params={"call_sid": "CAflow1"})
    assert live.status_code == 200
    body = live.json()
    assert body["status"] == "in-progress"
    assert body["terminal"] is False
    assert body["history"] == ["queued", "in-progress"]

    call_registry.update_status("CAflow1", "completed", duration="42")
    done = client.get("/twilio/call-status", params={"call_sid": "CAflow1"})
    body = done.json()
    assert body["status"] == "completed"
    assert body["terminal"] is True
    assert body["duration"] == "42"
    call_registry.clear()


def test_status_callback_updates_registry(client, monkeypatch):
    monkeypatch.setenv("TWILIO_VALIDATE_SIGNATURES", "false")
    reset_settings_cache()
    call_registry.clear()
    call_registry.record_call(
        "CAcb1",
        to="+919888877777",
        from_number="+15551234567",
        session_id="sess-cb",
        status="queued",
    )
    response = client.post(
        "/twilio/status-callback",
        data={"CallSid": "CAcb1", "CallStatus": "answered", "CallDuration": ""},
    )
    assert response.status_code == 200
    entry = call_registry.get_call("CAcb1")
    assert entry["status"] == "answered"
    call_registry.clear()
