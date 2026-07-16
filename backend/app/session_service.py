"""In-memory session store and utterance processing orchestration."""

from __future__ import annotations

import time
from threading import Lock

from fastapi import HTTPException

from app.config import get_settings
from app.faq import (
    SAFE_FALLBACK,
    answer_faq,
    education_prompt,
    introduction_prompt,
)
from app.logging_setup import get_logger
from app.models import (
    AgentReply,
    CreateSessionRequest,
    FlowBucket,
    Intent,
    Language,
    SessionResponse,
    SessionState,
    TranscriptTurn,
    UtteranceRequest,
)
from app.projects import get_project
from app.router import route_utterance
from app.state import apply_flow_transition
from app.summary import generate_summary

logger = get_logger(__name__)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}
        self._lock = Lock()

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
            fresh = SessionState(session_id=session_id, project_id=project_id, language=language)
            self._sessions[session_id] = fresh
            return fresh


store = SessionStore()


def create_session(payload: CreateSessionRequest) -> SessionResponse:
    settings = get_settings()
    project_id = (payload.project_id or settings.default_project).lower()
    if get_project(project_id) is None:
        raise HTTPException(status_code=400, detail=f"Unknown project_id: {project_id}")

    language = payload.language or Language(settings.default_language)
    session = SessionState(project_id=project_id, language=language)
    intro_text, faq_source = introduction_prompt(project_id, language)
    session.transcript.append(
        TranscriptTurn(role="agent", text=intro_text, language=language, intent=Intent.GREETING)
    )
    session.last_faq_source = faq_source
    session.last_intent = Intent.GREETING
    store.create(session)

    reply = AgentReply(
        text=intro_text,
        faq_source=faq_source,
        flow_bucket=session.flow_bucket,
        language=session.language,
        intent=Intent.GREETING,
    )
    logger.info("session_created", extra={"session_id": session.session_id, "project_id": project_id})
    return SessionResponse(session=session, reply=reply, latency_ms=0.0)


def get_session(session_id: str) -> SessionResponse:
    return SessionResponse(session=store.get(session_id), reply=None, latency_ms=None)


def reset_session(session_id: str) -> SessionResponse:
    existing = store.get(session_id)
    fresh = store.reset(session_id, existing.project_id, existing.language)
    intro_text, faq_source = introduction_prompt(fresh.project_id, fresh.language)
    fresh.transcript.append(
        TranscriptTurn(role="agent", text=intro_text, language=fresh.language, intent=Intent.GREETING)
    )
    fresh.last_faq_source = faq_source
    fresh.last_intent = Intent.GREETING
    store.save(fresh)
    reply = AgentReply(
        text=intro_text,
        faq_source=faq_source,
        flow_bucket=fresh.flow_bucket,
        language=fresh.language,
        intent=Intent.GREETING,
    )
    return SessionResponse(session=fresh, reply=reply, latency_ms=0.0)


def process_utterance(session_id: str, payload: UtteranceRequest) -> SessionResponse:
    started = time.perf_counter()
    session = store.get(session_id)

    if payload.interrupt:
        session.is_interrupted = True
        session.previous_bucket = session.flow_bucket

    if payload.language is not None:
        session.language = payload.language

    user_text = payload.text.strip()
    route = route_utterance(user_text, session.project_id)

    session.transcript.append(
        TranscriptTurn(
            role="user",
            text=user_text,
            language=session.language,
            intent=route.intent,
        )
    )
    session.last_intent = route.intent

    _apply_slot_updates(session, route.extracted_slots)

    reply_text, faq_source, intent = _compose_reply(session, route)

    # AFFIRM already advances bucket inside _compose_reply for next_steps → summary.
    if intent != Intent.AFFIRM:
        apply_flow_transition(session, intent)

    if session.flow_bucket == FlowBucket.SUMMARY and not session.final_summary:
        session.final_summary = generate_summary(session)
        reply_text = session.final_summary
        faq_source = f"summary:{session.project_id}"

    session.last_faq_source = faq_source
    session.transcript.append(
        TranscriptTurn(
            role="agent",
            text=reply_text,
            language=session.language,
            intent=intent,
        )
    )
    session.is_interrupted = False
    store.save(session)

    latency_ms = (time.perf_counter() - started) * 1000
    reply = AgentReply(
        text=reply_text,
        faq_source=faq_source,
        flow_bucket=session.flow_bucket,
        language=session.language,
        intent=intent,
        needs_handoff=session.needs_handoff,
    )
    logger.info(
        "utterance_processed",
        extra={
            "session_id": session_id,
            "intent": intent.value,
            "latency_ms": round(latency_ms, 2),
        },
    )
    return SessionResponse(session=session, reply=reply, latency_ms=round(latency_ms, 2))


def _apply_slot_updates(session: SessionState, slots: dict) -> None:
    if "site_visit_preferred_day" in slots:
        session.memory.site_visit_preferred_day = slots["site_visit_preferred_day"]
        session.memory.site_visit_interest = True
    if "preferred_callback_time" in slots:
        session.memory.preferred_callback_time = slots["preferred_callback_time"]
    if "target_project_id" in slots and slots["target_project_id"]:
        pass  # handled in compose


def _compose_reply(session: SessionState, route) -> tuple[str, str | None, Intent]:
    intent = route.intent
    language = session.language

    if intent == Intent.LANGUAGE_SWITCH:
        new_lang = route.detected_language or Language(route.extracted_slots.get("language", language.value))
        session.language = new_lang
        text = {
            Language.EN: "Switched to English. How can I help with this project?",
            Language.TA: "தமிழுக்கு மாற்றினேன். இந்த திட்டத்தில் எப்படி உதவட்டுமா?",
            Language.TANGLISH: "Tanglish ku switch aachu. Ippo eppadi help panna?",
        }[new_lang]
        return text, f"system:language_switch:{new_lang.value}", intent

    if intent == Intent.CONTEXT_SWITCH and route.target_project_id:
        if get_project(route.target_project_id) is None:
            return SAFE_FALLBACK[language], "system:unknown_project", Intent.OUT_OF_DOMAIN
        session.previous_bucket = session.flow_bucket
        session.project_id = route.target_project_id
        session.flow_bucket = FlowBucket.EDUCATION
        text, source = education_prompt(session.project_id, language)
        return text, source, intent

    if intent == Intent.HUMAN_HANDOFF:
        session.needs_handoff = True
        text, source = answer_faq(intent, session.project_id, language)
        return text, source, intent

    if intent == Intent.SITE_VISIT:
        session.memory.site_visit_interest = True
        text, source = answer_faq(intent, session.project_id, language)
        return text, source, intent

    if intent == Intent.GREETING:
        text, source = introduction_prompt(session.project_id, language)
        return text, source, intent

    if intent == Intent.AFFIRM:
        if session.flow_bucket == FlowBucket.INTRODUCTION:
            text, source = education_prompt(session.project_id, language)
            return text, source, intent
        if session.flow_bucket == FlowBucket.EDUCATION:
            text, source = answer_faq(Intent.SITE_VISIT, session.project_id, language)
            session.memory.site_visit_interest = True
            return text, source, Intent.SITE_VISIT
        if session.flow_bucket == FlowBucket.NEXT_STEPS:
            session.flow_bucket = FlowBucket.SUMMARY
            summary = generate_summary(session)
            session.final_summary = summary
            return summary, f"summary:{session.project_id}", intent
        summary = session.final_summary or generate_summary(session)
        session.final_summary = summary
        return summary, f"summary:{session.project_id}", intent

    if intent in {
        Intent.PROJECT_INFO,
        Intent.PRICING,
        Intent.LOCATION,
        Intent.AMENITIES,
        Intent.CALLBACK,
        Intent.OUT_OF_DOMAIN,
    }:
        text, source = answer_faq(intent, session.project_id, language)
        return text, source, intent

    text, source = answer_faq(Intent.OUT_OF_DOMAIN, session.project_id, language)
    return text, source, Intent.OUT_OF_DOMAIN
