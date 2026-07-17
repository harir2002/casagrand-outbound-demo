"""In-memory registry of outbound calls (local demo; no persistence)."""

from __future__ import annotations

import threading
import time
from typing import Any

_TERMINAL_STATUSES = {"completed", "failed", "busy", "no-answer", "canceled"}

_lock = threading.Lock()
_calls: dict[str, dict[str, Any]] = {}


def record_call(
    call_sid: str,
    *,
    to: str,
    from_number: str,
    session_id: str,
    status: str,
) -> None:
    with _lock:
        _calls[call_sid] = {
            "call_sid": call_sid,
            "to": to,
            "from_number": from_number,
            "session_id": session_id,
            "status": status,
            "duration": None,
            "updated_at": time.time(),
            "history": [status],
        }


def update_status(call_sid: str, status: str, *, duration: str | None = None) -> None:
    if not call_sid or not status:
        return
    with _lock:
        entry = _calls.get(call_sid)
        if entry is None:
            entry = {
                "call_sid": call_sid,
                "to": None,
                "from_number": None,
                "session_id": None,
                "status": status,
                "duration": duration,
                "updated_at": time.time(),
                "history": [status],
            }
            _calls[call_sid] = entry
            return
        entry["status"] = status
        entry["updated_at"] = time.time()
        if duration is not None:
            entry["duration"] = duration
        if not entry["history"] or entry["history"][-1] != status:
            entry["history"].append(status)


def get_call(call_sid: str) -> dict[str, Any] | None:
    with _lock:
        entry = _calls.get(call_sid)
        return dict(entry) if entry else None


def is_terminal(status: str | None) -> bool:
    return (status or "").lower() in _TERMINAL_STATUSES


def clear() -> None:
    with _lock:
        _calls.clear()
