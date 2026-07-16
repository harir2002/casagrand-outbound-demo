import pytest

from app.core.config import Settings, reset_settings_cache
from app.providers.errors import ProviderConfigError
from app.providers.factory import (
    build_provider_bundle,
    resolve_llm_name,
    resolve_stt_name,
    resolve_tts_name,
    validate_live_provider_config,
)
from app.providers.llm.groq_llm import GroqLLM
from app.providers.stt.sarvam_stt import SarvamSTT
from app.providers.tts.hybrid_sarvam_tts import HybridSarvamTTS
from app.providers.tts.sarvam_tts import SarvamTTS
from app.providers.tts.sarvam_tts_ws import SarvamStreamingTTS
from tests.doubles.providers import StubLLM, StubSTT, StubTTS


def test_live_mode_requires_keys(monkeypatch):
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("PROVIDER_MODE", "live")
    monkeypatch.setenv("ALLOW_TEST_STUBS", "false")
    monkeypatch.setenv("STT_PROVIDER", "sarvam")
    monkeypatch.setenv("TTS_PROVIDER", "sarvam")
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("SARVAM_API_KEY", "")
    monkeypatch.setenv("GROQ_API_KEY", "")
    reset_settings_cache()

    settings = Settings()
    problems = validate_live_provider_config(settings)
    assert any("SARVAM_API_KEY" in p for p in problems)
    assert any("GROQ_API_KEY" in p for p in problems)
    with pytest.raises(ProviderConfigError):
        build_provider_bundle(settings)


def test_live_mode_selects_real_providers_when_keys_present(monkeypatch):
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("PROVIDER_MODE", "live")
    monkeypatch.setenv("ALLOW_TEST_STUBS", "false")
    monkeypatch.setenv("STT_PROVIDER", "sarvam")
    monkeypatch.setenv("TTS_PROVIDER", "sarvam")
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("SARVAM_API_KEY", "test-sarvam")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq")
    monkeypatch.setenv("SARVAM_TTS_STREAMING", "true")
    reset_settings_cache()

    settings = Settings()
    assert validate_live_provider_config(settings) == []
    assert resolve_stt_name(settings) == "sarvam"
    assert resolve_tts_name(settings) == "sarvam"
    assert resolve_llm_name(settings) == "groq"

    bundle = build_provider_bundle(settings)
    assert isinstance(bundle.stt, SarvamSTT)
    assert isinstance(bundle.tts, HybridSarvamTTS)
    assert isinstance(bundle.tts.http, SarvamTTS)
    assert isinstance(bundle.tts.streaming, SarvamStreamingTTS)
    assert bundle.tts.prefer_streaming is True
    assert isinstance(bundle.llm, GroqLLM)
    assert bundle.mode == "live"


def test_http_only_tts_backup_when_streaming_disabled(monkeypatch):
    monkeypatch.setenv("PROVIDER_MODE", "live")
    monkeypatch.setenv("ALLOW_TEST_STUBS", "false")
    monkeypatch.setenv("STT_PROVIDER", "sarvam")
    monkeypatch.setenv("TTS_PROVIDER", "sarvam")
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("SARVAM_API_KEY", "test-sarvam")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq")
    monkeypatch.setenv("SARVAM_TTS_STREAMING", "false")
    reset_settings_cache()

    settings = Settings()
    bundle = build_provider_bundle(settings)
    assert isinstance(bundle.tts, HybridSarvamTTS)
    assert bundle.tts.prefer_streaming is False
    assert bundle.tts.streaming is None
    assert isinstance(bundle.tts.http, SarvamTTS)


def test_test_mode_allows_stubs(monkeypatch):
    monkeypatch.setenv("PROVIDER_MODE", "test")
    monkeypatch.setenv("ALLOW_TEST_STUBS", "true")
    monkeypatch.setenv("STT_PROVIDER", "stub")
    monkeypatch.setenv("TTS_PROVIDER", "stub")
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    reset_settings_cache()

    settings = Settings()
    assert validate_live_provider_config(settings) == []
    bundle = build_provider_bundle(settings)
    assert isinstance(bundle.stt, StubSTT)
    assert isinstance(bundle.tts, StubTTS)
    assert isinstance(bundle.llm, StubLLM)
    assert bundle.mode == "test"


def test_live_mode_rejects_explicit_stub_selection(monkeypatch):
    monkeypatch.setenv("PROVIDER_MODE", "live")
    monkeypatch.setenv("ALLOW_TEST_STUBS", "false")
    monkeypatch.setenv("STT_PROVIDER", "stub")
    monkeypatch.setenv("TTS_PROVIDER", "sarvam")
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("SARVAM_API_KEY", "k")
    monkeypatch.setenv("GROQ_API_KEY", "k")
    reset_settings_cache()

    settings = Settings()
    problems = validate_live_provider_config(settings)
    assert problems
    with pytest.raises(ProviderConfigError):
        resolve_stt_name(settings)
