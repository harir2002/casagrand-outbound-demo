from app.models.session import Intent, Language, MemorySlots, SessionState
from app.services.summary_service import generate_summary


def test_summary_includes_project_and_slots():
    session = SessionState(
        project_id="highcity",
        language=Language.EN,
        last_intent=Intent.SITE_VISIT,
        memory=MemorySlots(
            site_visit_interest=True,
            site_visit_preferred_day="saturday",
            preferred_callback_time="5 pm",
            brochure_requested=True,
        ),
    )
    summary = generate_summary(session)
    assert "Highcity" in summary
    assert "saturday" in summary
    assert "5 pm" in summary
    assert "Brochure requested: yes" in summary


def test_summary_tamil_variant():
    session = SessionState(
        project_id="mercury",
        language=Language.TA,
        last_intent=Intent.CALLBACK,
    )
    summary = generate_summary(session)
    assert "சுருக்கம்" in summary
    assert "Mercury" in summary
