import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.session_service import store


@pytest.fixture(autouse=True)
def clear_sessions():
    store._sessions.clear()
    yield
    store._sessions.clear()


@pytest.fixture
def client():
    return TestClient(app)
