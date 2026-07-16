import pytest
from fastapi.testclient import TestClient

from app.core.config import reset_settings_cache
from app.main import create_app
from app.services.conversation_orchestrator import reset_orchestrator
from app.services.session_store import store


@pytest.fixture(autouse=True)
def _isolate_providers(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("PROVIDER_MODE", "test")
    monkeypatch.setenv("ALLOW_TEST_STUBS", "true")
    monkeypatch.setenv("STT_PROVIDER", "stub")
    monkeypatch.setenv("TTS_PROVIDER", "stub")
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    monkeypatch.setenv("SARVAM_API_KEY", "")
    monkeypatch.setenv("GROQ_API_KEY", "")
    reset_settings_cache()
    reset_orchestrator()
    yield
    reset_settings_cache()
    reset_orchestrator()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    store.clear()
    with TestClient(app) as test_client:
        yield test_client
    store.clear()
