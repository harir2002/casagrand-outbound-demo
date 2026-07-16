"""Shared provider result models."""

from dataclasses import dataclass, field
from typing import Any

from app.models.session import Language


@dataclass
class TranscriptResult:
    text: str
    language: Language | None = None
    confidence: float = 1.0
    provider: str = "unknown"
    latency_ms: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class SynthesisResult:
    text: str
    audio_base64: str | None = None
    audio_url: str | None = None
    mime_type: str = "audio/wav"
    provider: str = "unknown"
    latency_ms: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class LlmResult:
    text: str
    provider: str = "unknown"
    latency_ms: float = 0.0
    meta: dict[str, Any] = field(default_factory=dict)
