"""TwiML generation tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import reset_settings_cache
from app.integrations.twilio.twiml import build_media_stream_twiml, build_say_fallback_twiml


def test_media_stream_twiml_contains_connect_stream():
    xml = build_media_stream_twiml(
        "wss://demo.example.ngrok.app/twilio/media-stream",
        parameters={
            "session_id": "sess-1",
            "project_id": "highcity",
            "language": "en",
        },
    )
    assert xml.startswith("<?xml")
    assert "<Connect>" in xml
    assert "<Stream" in xml
    assert 'url="wss://demo.example.ngrok.app/twilio/media-stream"' in xml
    assert 'name="session_id"' in xml
    assert 'value="sess-1"' in xml
    assert "</Response>" in xml


def test_say_fallback_twiml_escapes():
    xml = build_say_fallback_twiml('Missing <config> & "url"')
    assert "<Say>" in xml
    assert "<Hangup/>" in xml
    assert "<config>" not in xml


def test_voice_webhook_returns_stream_twiml(monkeypatch):
    monkeypatch.setenv("TWILIO_ENABLED", "true")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACxxxxxxxx")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+15551234567")
    monkeypatch.setenv("TWILIO_PUBLIC_BASE_URL", "https://demo.example.ngrok.app")
    monkeypatch.setenv("TWILIO_VALIDATE_SIGNATURES", "false")
    reset_settings_cache()
    from app.main import create_app

    with TestClient(create_app()) as twilio_client:
        response = twilio_client.get(
            "/twilio/voice-webhook",
            params={"project_id": "highcity", "language": "en"},
        )
    assert response.status_code == 200
    assert "application/xml" in response.headers.get("content-type", "")
    body = response.text
    assert "<Stream" in body
    assert "wss://demo.example.ngrok.app/twilio/media-stream" in body


def test_voice_webhook_fallback_when_disabled(monkeypatch):
    monkeypatch.setenv("TWILIO_ENABLED", "false")
    reset_settings_cache()
    from app.main import create_app

    with TestClient(create_app()) as twilio_client:
        response = twilio_client.get("/twilio/voice-webhook")
    assert response.status_code == 200
    assert "<Say>" in response.text
