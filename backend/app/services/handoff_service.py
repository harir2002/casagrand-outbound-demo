"""Human handoff escalation payload builder."""

from __future__ import annotations

from app.core.logging import get_logger
from app.data.projects import get_project
from app.models.session import HandoffPayload, SessionState
from app.services.summary_service import generate_summary

logger = get_logger(__name__)


def build_handoff_payload(
    session: SessionState,
    reason: str = "caller_requested_human",
) -> HandoffPayload:
    project = get_project(session.project_id)
    project_name = project.name if project else session.project_id
    summary = session.final_summary or generate_summary(session)

    excerpt: list[str] = []
    for turn in session.transcript[-6:]:
        excerpt.append(f"{turn.role}: {turn.text}")

    payload = HandoffPayload(
        session_id=session.session_id,
        project_id=session.project_id,
        project_name=project_name,
        language=session.language,
        flow_bucket=session.flow_bucket,
        reason=reason,
        memory=session.memory,
        last_intent=session.last_intent,
        transcript_excerpt=excerpt,
        summary=summary,
    )
    logger.info(
        "handoff_created session=%s project=%s reason=%s",
        session.session_id,
        session.project_id,
        reason,
    )
    return payload


def format_handoff_message(payload: HandoffPayload) -> str:
    return (
        f"HANDOFF | session={payload.session_id} | project={payload.project_name} "
        f"({payload.project_id}) | language={payload.language.value} | "
        f"bucket={payload.flow_bucket.value} | reason={payload.reason}\n"
        f"Summary: {payload.summary}\n"
        f"Recent turns:\n" + "\n".join(payload.transcript_excerpt)
    )
