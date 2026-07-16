"""Call orchestration across router, FAQ, state machine, summary, handoff."""

from __future__ import annotations

import time

from fastapi import HTTPException

from app.core.config import get_settings
from app.core.logging import get_logger
from app.data.projects import get_project
from app.models.session import (
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
from app.services.faq_service import faq_service
from app.services.handoff_service import build_handoff_payload
from app.services.intent_router import route_utterance
from app.services.session_store import store
from app.services.state_machine import apply_intent_transition, transition_to
from app.services.summary_service import generate_summary

logger = get_logger(__name__)


def create_session(payload: CreateSessionRequest) -> SessionResponse:
    settings = get_settings()
    project_id = (payload.project_id or settings.default_project).lower()
    if get_project(project_id) is None:
        raise HTTPException(status_code=400, detail=f"Unknown project_id: {project_id}")

    language = payload.language or Language(settings.default_language)
    session = SessionState(project_id=project_id, language=language)
    intro = faq_service.introduction(project_id, language)
    session.transcript.append(
        TranscriptTurn(
            role="agent",
            text=intro.text,
            language=language,
            intent=Intent.GREETING,
        )
    )
    session.last_faq_source = intro.source
    session.last_intent = Intent.GREETING
    store.create(session)

    reply = AgentReply(
        text=intro.text,
        faq_source=intro.source,
        flow_bucket=session.flow_bucket,
        language=session.language,
        intent=Intent.GREETING,
    )
    logger.info("session_created session=%s project=%s", session.session_id, project_id)
    return SessionResponse(session=session, reply=reply, latency_ms=0.0)


def get_session(session_id: str) -> SessionResponse:
    return SessionResponse(session=store.get(session_id), reply=None, latency_ms=None)


def reset_session(session_id: str) -> SessionResponse:
    existing = store.get(session_id)
    fresh = store.reset(session_id, existing.project_id, existing.language)
    intro = faq_service.introduction(fresh.project_id, fresh.language)
    fresh.transcript.append(
        TranscriptTurn(
            role="agent",
            text=intro.text,
            language=fresh.language,
            intent=Intent.GREETING,
        )
    )
    fresh.last_faq_source = intro.source
    fresh.last_intent = Intent.GREETING
    store.save(fresh)
    reply = AgentReply(
        text=intro.text,
        faq_source=intro.source,
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

    if intent != Intent.AFFIRM:
        apply_intent_transition(session, intent)

    if session.flow_bucket == FlowBucket.CLOSING_SUMMARY and not session.final_summary:
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

    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    reply = AgentReply(
        text=reply_text,
        faq_source=faq_source,
        flow_bucket=session.flow_bucket,
        language=session.language,
        intent=intent,
        needs_handoff=session.needs_handoff,
    )
    logger.info(
        "utterance_processed session=%s intent=%s latency_ms=%s",
        session_id,
        intent.value,
        latency_ms,
    )
    return SessionResponse(session=session, reply=reply, latency_ms=latency_ms)


def _apply_slot_updates(session: SessionState, slots: dict) -> None:
    if "site_visit_preferred_day" in slots:
        session.memory.site_visit_preferred_day = slots["site_visit_preferred_day"]
        session.memory.site_visit_interest = True
    if "preferred_callback_time" in slots:
        session.memory.preferred_callback_time = slots["preferred_callback_time"]


def _compose_reply(session: SessionState, route) -> tuple[str, str | None, Intent]:
    intent = route.intent
    language = session.language

    if intent == Intent.LANGUAGE_SWITCH:
        new_lang = route.detected_language or Language(
            route.extracted_slots.get("language", language.value)
        )
        session.language = new_lang
        text = {
            Language.EN: "Switched to English. How can I help with this project?",
            Language.TA: "தமிழுக்கு மாற்றினேன். இந்த திட்டத்தில் எப்படி உதவட்டுமா?",
            Language.TANGLISH: "Tanglish ku switch aachu. Ippo eppadi help panna?",
        }[new_lang]
        return text, f"system:language_switch:{new_lang.value}", intent

    if intent == Intent.CONTEXT_SWITCH and route.target_project_id:
        if get_project(route.target_project_id) is None:
            result = faq_service.lookup(Intent.OUT_OF_DOMAIN, session.project_id, language)
            return result.text, result.source, Intent.OUT_OF_DOMAIN
        session.project_id = route.target_project_id
        transition_to(session, FlowBucket.EDUCATION, "context_switch")
        result = faq_service.education(session.project_id, language)
        return result.text, result.source, intent

    if intent == Intent.HUMAN_HANDOFF:
        session.needs_handoff = True
        payload = build_handoff_payload(session)
        session.handoff_payload = payload.model_dump(mode="json")
        result = faq_service.lookup(intent, session.project_id, language)
        return result.text, result.source, intent

    if intent == Intent.SITE_VISIT:
        session.memory.site_visit_interest = True
        result = faq_service.lookup(intent, session.project_id, language)
        return result.text, result.source, intent

    if intent == Intent.BROCHURE:
        session.memory.brochure_requested = True
        result = faq_service.lookup(intent, session.project_id, language)
        return result.text, result.source, intent

    if intent == Intent.GREETING:
        result = faq_service.introduction(session.project_id, language)
        return result.text, result.source, intent

    if intent == Intent.AFFIRM:
        if session.flow_bucket == FlowBucket.INTRODUCTION:
            transition_to(session, FlowBucket.EDUCATION, "affirm_intro")
            result = faq_service.education(session.project_id, language)
            return result.text, result.source, intent
        if session.flow_bucket == FlowBucket.EDUCATION:
            transition_to(session, FlowBucket.NEXT_STEPS, "affirm_education")
            session.memory.site_visit_interest = True
            result = faq_service.lookup(Intent.SITE_VISIT, session.project_id, language)
            return result.text, result.source, Intent.SITE_VISIT
        if session.flow_bucket == FlowBucket.NEXT_STEPS:
            transition_to(session, FlowBucket.CLOSING_SUMMARY, "affirm_next_steps")
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
        result = faq_service.lookup(intent, session.project_id, language)
        return result.text, result.source, intent

    result = faq_service.lookup(Intent.OUT_OF_DOMAIN, session.project_id, language)
    return result.text, result.source, Intent.OUT_OF_DOMAIN
