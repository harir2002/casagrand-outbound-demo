from app.core.config import Settings, reset_settings_cache
from app.providers.factory import validate_live_provider_config


def test_real_mode_config_valid_with_keys(monkeypatch):
    monkeypatch.setenv("PROVIDER_MODE", "live")
    monkeypatch.setenv("ALLOW_TEST_STUBS", "false")
    monkeypatch.setenv("STT_PROVIDER", "sarvam")
    monkeypatch.setenv("TTS_PROVIDER", "sarvam")
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("SARVAM_API_KEY", "sarvam-live")
    monkeypatch.setenv("GROQ_API_KEY", "groq-live")
    reset_settings_cache()

    settings = Settings()
    assert settings.is_test_provider_mode is False
    assert validate_live_provider_config(settings) == []


def test_real_mode_config_invalid_without_keys(monkeypatch):
    monkeypatch.setenv("PROVIDER_MODE", "live")
    monkeypatch.setenv("ALLOW_TEST_STUBS", "false")
    monkeypatch.setenv("TTS_PROVIDER", "sarvam")
    monkeypatch.setenv("SARVAM_API_KEY", "")
    monkeypatch.setenv("GROQ_API_KEY", "")
    reset_settings_cache()

    settings = Settings()
    problems = validate_live_provider_config(settings)
    assert len(problems) >= 2


def test_health_reports_provider_readiness_in_test_mode(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["provider_mode"] == "test"
    assert body["providers_ready"] is True
    assert body["provider_errors"] == []
