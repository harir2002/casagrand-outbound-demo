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
    callback = (
        memory.callback_choice
        or memory.preferred_callback_time
        or "not specified"
    )
    brochure = "yes" if memory.brochure_requested else "no"
    handoff = "requested" if session.needs_handoff else "not requested"
    reason = f" ({memory.handoff_reason})" if memory.handoff_reason else ""
    customer_name = memory.customer_name or memory.caller_name
    customer = f"Customer: {customer_name}. " if customer_name else ""
    unit = memory.unit_preference or "not specified"
    budget = memory.budget_band or memory.budget_mentioned or "not specified"

    if language == Language.TA:
        return (
            f"{customer}சுருக்கம்: திட்டம் {project_name}. மொழி: {language.value}. "
            f"Unit: {unit}. Budget: {budget}. "
            f"தள வருகை ஆர்வம்: {visit} (நாள்: {day}). "
            f"கால்பேக்: {callback}. Brochure: {brochure}. "
            f"Handoff: {handoff}{reason}. கடைசி intent: {session.last_intent}."
        )
    if language == Language.TANGLISH:
        return (
            f"{customer}Summary: Project {project_name}. Language: {language.value}. "
            f"Unit: {unit}. Budget: {budget}. "
            f"Site visit interest: {visit} (day: {day}). "
            f"Callback: {callback}. Brochure: {brochure}. "
            f"Handoff: {handoff}{reason}. Last intent: {session.last_intent}."
        )
    return (
        f"{customer}Summary: Discussed {project_name}. Language: {language.value}. "
        f"Unit preference: {unit}. Budget band: {budget}. "
        f"Site-visit interest: {visit} (preferred day: {day}). "
        f"Callback preference: {callback}. Brochure requested: {brochure}. "
        f"Human handoff: {handoff}{reason}. Last intent: {session.last_intent}."
    )
