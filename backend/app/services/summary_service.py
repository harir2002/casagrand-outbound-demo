"""Structured closing summary from session state."""

from __future__ import annotations

from app.data.projects import get_project
from app.models.session import Language, SessionState


def generate_summary(session: SessionState) -> str:
    project = get_project(session.project_id)
    project_name = project.name if project else session.project_id
    memory = session.memory
    language = session.language

    visit = "yes" if memory.site_visit_interest else "not confirmed"
    day = memory.site_visit_preferred_day or "not specified"
    callback = memory.preferred_callback_time or "not specified"
    brochure = "yes" if memory.brochure_requested else "no"
    handoff = "requested" if session.needs_handoff else "not requested"

    if language == Language.TA:
        return (
            f"சுருக்கம்: திட்டம் {project_name}. மொழி: {language.value}. "
            f"தள வருகை ஆர்வம்: {visit} (நாள்: {day}). "
            f"கால்பேக்: {callback}. Brochure: {brochure}. "
            f"Handoff: {handoff}. கடைசி intent: {session.last_intent}."
        )
    if language == Language.TANGLISH:
        return (
            f"Summary: Project {project_name}. Language: {language.value}. "
            f"Site visit interest: {visit} (day: {day}). "
            f"Callback: {callback}. Brochure: {brochure}. "
            f"Handoff: {handoff}. Last intent: {session.last_intent}."
        )
    return (
        f"Summary: Discussed {project_name}. Language: {language.value}. "
        f"Site-visit interest: {visit} (preferred day: {day}). "
        f"Callback preference: {callback}. Brochure requested: {brochure}. "
        f"Human handoff: {handoff}. Last intent: {session.last_intent}."
    )
