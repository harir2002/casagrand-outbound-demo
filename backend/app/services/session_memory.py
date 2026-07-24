"""Short-term call session memory — slots updated after each turn."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.session import Intent, Language, MemorySlots, SessionState


class SessionMemory(BaseModel):
    """Compact memory object for prompts, handoff, and smoke checks."""

    session_id: str
    active_language: Language
    active_project: str
    customer_name: str | None = None
    unit_preference: str | None = None
    budget_band: str | None = None
    callback_choice: str | None = None
    last_question: str | None = None
    needs_handoff: bool = False
    handoff_reason: str | None = None
    summary: str | None = None
    last_intent: Intent | None = None
    last_rag_sources: list[str] = Field(default_factory=list)

    def prompt_context(self) -> str:
        """Minimal fields for LLM phrasing — no invention of facts."""
        parts = [
            f"project={self.active_project}",
            f"language={self.active_language.value}",
        ]
        if self.customer_name:
            parts.append(f"customer={self.customer_name}")
        if self.unit_preference:
            parts.append(f"unit={self.unit_preference}")
        if self.budget_band:
            parts.append(f"budget={self.budget_band}")
        if self.callback_choice:
            parts.append(f"callback={self.callback_choice}")
        if self.needs_handoff:
            parts.append(f"handoff={self.handoff_reason or 'requested'}")
        return "; ".join(parts)


def to_session_memory(session: SessionState) -> SessionMemory:
    memory = session.memory
    return SessionMemory(
        session_id=session.session_id,
        active_language=session.language,
        active_project=session.project_id,
        customer_name=memory.caller_name or memory.customer_name,
        unit_preference=memory.unit_preference,
        budget_band=memory.budget_band or memory.budget_mentioned,
        callback_choice=memory.callback_choice or memory.preferred_callback_time,
        last_question=memory.last_question,
        needs_handoff=session.needs_handoff,
        handoff_reason=memory.handoff_reason,
        summary=memory.summary or session.final_summary,
        last_intent=session.last_intent,
        last_rag_sources=list(memory.last_rag_sources),
    )


def update_memory_after_turn(
    session: SessionState,
    *,
    user_text: str,
    intent: Intent,
    extracted_slots: dict | None = None,
    rag_sources: list[str] | None = None,
    handoff_reason: str | None = None,
    summary: str | None = None,
) -> SessionMemory:
    """Sync session.memory slots from STT/intent/RAG/LLM turn artifacts."""
    slots = extracted_slots or {}
    mem = session.memory

    mem.last_question = user_text.strip()[:500] or mem.last_question

    if slots.get("caller_name") or slots.get("customer_name"):
        name = slots.get("caller_name") or slots.get("customer_name")
        mem.caller_name = str(name)
        mem.customer_name = str(name)

    if slots.get("unit_preference"):
        mem.unit_preference = str(slots["unit_preference"])
    else:
        unit = _extract_unit_preference(user_text)
        if unit:
            mem.unit_preference = unit

    if slots.get("budget_band") or slots.get("budget_mentioned"):
        band = slots.get("budget_band") or slots.get("budget_mentioned")
        mem.budget_band = str(band)
        mem.budget_mentioned = str(band)

    if slots.get("preferred_callback_time") or slots.get("callback_choice"):
        choice = slots.get("callback_choice") or slots.get("preferred_callback_time")
        mem.callback_choice = str(choice)
        mem.preferred_callback_time = str(choice)

    if slots.get("site_visit_preferred_day"):
        mem.site_visit_preferred_day = str(slots["site_visit_preferred_day"])
        mem.site_visit_interest = True

    if rag_sources:
        mem.last_rag_sources = list(rag_sources)[:8]

    if handoff_reason:
        mem.handoff_reason = handoff_reason
    elif session.needs_handoff and not mem.handoff_reason:
        mem.handoff_reason = "caller_requested_human"

    if summary:
        mem.summary = summary
    elif session.final_summary:
        mem.summary = session.final_summary

    # Mirror active language / project into notes lightly for handoff dumps
    mem.customer_name = mem.customer_name or mem.caller_name

    session.last_intent = intent
    return to_session_memory(session)


def _extract_unit_preference(text: str) -> str | None:
    lowered = text.lower()
    if "3" in lowered and "bhk" in lowered:
        return "3BHK"
    if "2" in lowered and "bhk" in lowered:
        return "2BHK"
    if "studio" in lowered:
        return "studio"
    return None
