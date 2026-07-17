"""Twilio config validation tests (no network)."""

from __future__ import annotations

from app.core.config import reset_settings_cache
from app.integrations.twilio.config import (
    load_twilio_config,
    require_twilio_ready,
    validate_twilio_config,
)


def test_twilio_disabled_has_no_problems(monkeypatch):
    monkeypatch.setenv("TWILIO_ENABLED", "false")
    monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
    reset_settings_cache()
    cfg = load_twilio_config()
    assert cfg.enabled is False
    assert validate_twilio_config(cfg) == []


def test_twilio_enabled_missing_credentials(monkeypatch):
    monkeypatch.setenv("TWILIO_ENABLED", "true")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "")
    monkeypatch.setenv("TWILIO_PUBLIC_BASE_URL", "")
    reset_settings_cache()
    problems = validate_twilio_config()
    assert any("TWILIO_ACCOUNT_SID" in p for p in problems)
    assert any("TWILIO_AUTH_TOKEN" in p for p in problems)
    assert any("TWILIO_FROM_NUMBER" in p for p in problems)
    assert any("TWILIO_PUBLIC_BASE_URL" in p for p in problems)


def test_twilio_enabled_ready(monkeypatch):
    monkeypatch.setenv("TWILIO_ENABLED", "true")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACxxxxxxxx")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+15551234567")
    monkeypatch.setenv("TWILIO_PUBLIC_BASE_URL", "https://demo.example.ngrok.app")
    monkeypatch.setenv("TWILIO_MEDIA_STREAM_PATH", "/twilio/media-stream")
    reset_settings_cache()
    cfg = require_twilio_ready()
    assert cfg.enabled is True
    assert cfg.voice_webhook_url.endswith("/twilio/voice-webhook")
    assert cfg.media_stream_wss_url.startswith("wss://")
    assert "/twilio/media-stream" in cfg.media_stream_wss_url


def test_require_twilio_ready_when_disabled(monkeypatch):
    monkeypatch.setenv("TWILIO_ENABLED", "false")
    reset_settings_cache()
    try:
        require_twilio_ready()
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "disabled" in str(exc).lower()
