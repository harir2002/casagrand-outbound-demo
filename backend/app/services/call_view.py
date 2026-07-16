"""Map internal SessionResponse into the public CallView contract."""

from __future__ import annotations

from app.models.call_view import CallViewResponse
from app.models.session import FlowBucket, Intent, SessionResponse, SessionState


def derive_call_status(session: SessionState) -> str:
    if session.needs_handoff:
        return "handoff"
    if session.flow_bucket == FlowBucket.CLOSING_SUMMARY and session.final_summary:
        return "completed"
    if session.last_intent == Intent.OUT_OF_DOMAIN:
        return "fallback"
    return "active"


def to_call_view(result: SessionResponse) -> CallViewResponse:
    session = result.session
    handoff_reason = None
    if session.handoff_payload and isinstance(session.handoff_payload, dict):
        handoff_reason = session.handoff_payload.get("reason")

    reply_text = result.reply.text if result.reply else None
    faq_source = (
        result.reply.faq_source
        if result.reply and result.reply.faq_source
        else session.last_faq_source
    )

    return CallViewResponse(
        session_id=session.session_id,
        call_id=session.session_id,
        active_project=session.project_id,
        active_bucket=session.flow_bucket,
        active_language=session.language,
        previous_bucket=session.previous_bucket,
        transcript=session.transcript,
        memory_slots=session.memory,
        last_intent=session.last_intent,
        faq_source=faq_source,
        summary=session.final_summary,
        reply_text=reply_text,
        needs_handoff=session.needs_handoff,
        handoff_reason=handoff_reason,
        handoff_payload=session.handoff_payload,
        call_status=derive_call_status(session),
        is_interrupted=session.is_interrupted,
        latency_ms=result.latency_ms,
    )
