"""Shared streaming event / chunk models for voice pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AudioChunk:
    """One progressive TTS audio piece (WAV-wrapped for browser playback)."""

    audio_base64: str
    mime_type: str = "audio/wav"
    index: int = 0
    pcm_bytes: bytes | None = None
    meta: dict[str, Any] = field(default_factory=dict)


def stream_event(event: str, **payload: Any) -> dict[str, Any]:
    """Frontend-friendly NDJSON event envelope."""
    body: dict[str, Any] = {"event": event}
    body.update(payload)
    return body
