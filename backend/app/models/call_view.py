"""Stable call-view contract shared by local frontend integration."""

from typing import Any

from pydantic import BaseModel, Field

from app.models.session import (
    FlowBucket,
    Intent,
    Language,
    MemorySlots,
    TranscriptTurn,
)


class StartSessionRequest(BaseModel):
    project_id: str | None = None
    language: Language | None = None


class TurnRequest(BaseModel):
    session_id: str
    text: str | None = Field(default=None, max_length=2000)
    language: Language | None = None
    interrupt: bool = False
    audio_base64: str | None = None
    audio_mime_type: str | None = "audio/wav"
    skip_llm: bool = False


class ResetRequest(BaseModel):
    session_id: str


class StateQuery(BaseModel):
    session_id: str


class CallViewResponse(BaseModel):
    """Flat JSON payload consumed by the React demo UI."""

    session_id: str
    call_id: str
    active_project: str
    active_bucket: FlowBucket
    active_language: Language
    previous_bucket: FlowBucket | None = None
    transcript: list[TranscriptTurn] = Field(default_factory=list)
    memory_slots: MemorySlots = Field(default_factory=MemorySlots)
    last_intent: Intent | None = None
    faq_source: str | None = None
    summary: str | None = None
    reply_text: str | None = None
    needs_handoff: bool = False
    handoff_reason: str | None = None
    handoff_payload: dict[str, Any] | None = None
    call_status: str = "active"
    is_interrupted: bool = False
    latency_ms: float | None = None
    warning: str | None = None
    error: str | None = None
    # Provider / audio fields (optional for text-only clients)
    stt_provider: str | None = None
    tts_provider: str | None = None
    llm_provider: str | None = None
    audio_base64: str | None = None
    audio_url: str | None = None
    audio_mime_type: str | None = None
    stt_latency_ms: float | None = None
    llm_latency_ms: float | None = None
    tts_latency_ms: float | None = None
    provider_meta: dict[str, Any] = Field(default_factory=dict)