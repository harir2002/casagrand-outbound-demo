"""Unit test for CallView mapping."""

from app.models.session import (
    AgentReply,
    FlowBucket,
    Intent,
    Language,
    SessionResponse,
    SessionState,
)
from app.services.call_view import derive_call_status, to_call_view


def test_derive_call_status_variants():
    base = SessionState(project_id="highcity")
    assert derive_call_status(base) == "active"

    base.needs_handoff = True
    assert derive_call_status(base) == "handoff"

    base.needs_handoff = False
    base.last_intent = Intent.OUT_OF_DOMAIN
    assert derive_call_status(base) == "fallback"

    base.last_intent = Intent.AFFIRM
    base.flow_bucket = FlowBucket.CLOSING_SUMMARY
    base.final_summary = "done"
    assert derive_call_status(base) == "completed"


def test_to_call_view_flattens_session():
    session = SessionState(
        project_id="avenuepark",
        language=Language.EN,
        flow_bucket=FlowBucket.EDUCATION,
        last_intent=Intent.PRICING,
        last_faq_source="projects@demo:avenuepark:pricing",
        handoff_payload={"reason": "caller_requested_human"},
        needs_handoff=True,
    )
    result = SessionResponse(
        session=session,
        reply=AgentReply(
            text="pricing answer",
            faq_source="projects@demo:avenuepark:pricing",
            flow_bucket=FlowBucket.EDUCATION,
            language=Language.EN,
            intent=Intent.PRICING,
            needs_handoff=True,
        ),
        latency_ms=12.5,
    )
    view = to_call_view(result)
    assert view.session_id == view.call_id
    assert view.active_project == "avenuepark"
    assert view.active_bucket == FlowBucket.EDUCATION
    assert view.reply_text == "pricing answer"
    assert view.faq_source.endswith("pricing")
    assert view.handoff_reason == "caller_requested_human"
    assert view.call_status == "handoff"
    assert view.latency_ms == 12.5
