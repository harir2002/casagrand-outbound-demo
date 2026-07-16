from app.models.session import Intent, Language, MemorySlots, SessionState
from app.services.handoff_service import build_handoff_payload, format_handoff_message


def test_handoff_payload_structure():
    session = SessionState(
        project_id="avenuepark",
        language=Language.EN,
        last_intent=Intent.HUMAN_HANDOFF,
        needs_handoff=True,
        memory=MemorySlots(site_visit_interest=True),
    )
    session.transcript = []
    payload = build_handoff_payload(session, reason="caller_requested_human")
    assert payload.project_id == "avenuepark"
    assert payload.project_name == "Casagrand Avenuepark"
    assert payload.reason == "caller_requested_human"
    assert "Avenuepark" in payload.summary


def test_handoff_message_readable():
    session = SessionState(project_id="highcity", language=Language.TANGLISH)
    payload = build_handoff_payload(session)
    message = format_handoff_message(payload)
    assert message.startswith("HANDOFF")
    assert "highcity" in message
    assert "Summary:" in message
