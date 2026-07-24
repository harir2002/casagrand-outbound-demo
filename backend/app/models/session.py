from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Language(str, Enum):
    EN = "en"
    TA = "ta"
    TANGLISH = "tanglish"


class FlowBucket(str, Enum):
    INTRODUCTION = "introduction"
    EDUCATION = "education"
    NEXT_STEPS = "next_steps"
    CLOSING_SUMMARY = "closing_summary"


class Intent(str, Enum):
    PROJECT_INFO = "project_info"
    PRICING = "pricing"
    LOCATION = "location"
    AMENITIES = "amenities"
    SITE_VISIT = "site_visit"
    CALLBACK = "callback"
    LANGUAGE_SWITCH = "language_switch"
    CONTEXT_SWITCH = "context_switch"
    OUT_OF_DOMAIN = "out_of_domain"
    HUMAN_HANDOFF = "human_handoff"
    GREETING = "greeting"
    AFFIRM = "affirm"
    BROCHURE = "brochure"
    COMPARISON = "comparison"
    UNKNOWN = "unknown"


class TranscriptTurn(BaseModel):
    role: str
    text: str
    language: Language | None = None
    intent: Intent | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MemorySlots(BaseModel):
    caller_name: str | None = None
    customer_name: str | None = None
    preferred_callback_time: str | None = None
    callback_choice: str | None = None
    site_visit_interest: bool | None = None
    site_visit_preferred_day: str | None = None
    budget_mentioned: str | None = None
    budget_band: str | None = None
    unit_preference: str | None = None
    brochure_requested: bool | None = None
    last_question: str | None = None
    handoff_reason: str | None = None
    summary: str | None = None
    last_rag_sources: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class SessionState(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    language: Language = Language.EN
    flow_bucket: FlowBucket = FlowBucket.INTRODUCTION
    previous_bucket: FlowBucket | None = None
    transcript: list[TranscriptTurn] = Field(default_factory=list)
    memory: MemorySlots = Field(default_factory=MemorySlots)
    last_intent: Intent | None = None
    last_faq_source: str | None = None
    needs_handoff: bool = False
    is_interrupted: bool = False
    final_summary: str | None = None
    handoff_payload: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)


class CreateSessionRequest(BaseModel):
    project_id: str | None = None
    language: Language | None = None


class UtteranceRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    language: Language | None = None
    interrupt: bool = False


class RouteResult(BaseModel):
    intent: Intent
    confidence: float
    detected_language: Language | None = None
    target_project_id: str | None = None
    extracted_slots: dict[str, Any] = Field(default_factory=dict)


class AgentReply(BaseModel):
    text: str
    faq_source: str | None = None
    flow_bucket: FlowBucket
    language: Language
    intent: Intent
    needs_handoff: bool = False


class SessionResponse(BaseModel):
    session: SessionState
    reply: AgentReply | None = None
    latency_ms: float | None = None


class HealthResponse(BaseModel):
    status: str
    version: str
    env: str
    provider_mode: str = "live"
    providers_ready: bool = True
    provider_errors: list[str] = Field(default_factory=list)
    stt_provider: str | None = None
    tts_provider: str | None = None
    llm_provider: str | None = None
    tts_voice_id: str | None = None
    tts_voice_name: str | None = None


class HandoffPayload(BaseModel):
    session_id: str
    project_id: str
    project_name: str
    language: Language
    flow_bucket: FlowBucket
    reason: str
    memory: MemorySlots
    last_intent: Intent | None
    transcript_excerpt: list[str]
    summary: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
