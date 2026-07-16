"""In-memory session store (local-first; no persistence)."""

from __future__ import annotations

from threading import Lock

from fastapi import HTTPException

from app.models.session import Language, SessionState


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}
        self._lock = Lock()

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()

    def create(self, session: SessionState) -> SessionState:
        with self._lock:
            self._sessions[session.session_id] = session
            return session

    def get(self, session_id: str) -> SessionState:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise HTTPException(status_code=404, detail="Session not found")
            return session.model_copy(deep=True)

    def save(self, session: SessionState) -> SessionState:
        with self._lock:
            session.touch()
            self._sessions[session.session_id] = session
            return session

    def reset(self, session_id: str, project_id: str, language: Language) -> SessionState:
        with self._lock:
            if session_id not in self._sessions:
                raise HTTPException(status_code=404, detail="Session not found")
            fresh = SessionState(
                session_id=session_id,
                project_id=project_id,
                language=language,
            )
            self._sessions[session_id] = fresh
            return fresh


store = SessionStore()
