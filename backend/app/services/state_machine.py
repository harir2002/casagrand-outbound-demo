"""Bucket-based call-flow state machine."""

from __future__ import annotations

from app.core.logging import get_logger
from app.models.session import FlowBucket, Intent, SessionState

logger = get_logger(__name__)

FLOW_ORDER: list[FlowBucket] = [
    FlowBucket.INTRODUCTION,
    FlowBucket.EDUCATION,
    FlowBucket.NEXT_STEPS,
    FlowBucket.CLOSING_SUMMARY,
]

EDUCATION_INTENTS = {
    Intent.PROJECT_INFO,
    Intent.PRICING,
    Intent.LOCATION,
    Intent.AMENITIES,
    Intent.CONTEXT_SWITCH,
}

NEXT_STEPS_INTENTS = {
    Intent.SITE_VISIT,
    Intent.CALLBACK,
    Intent.BROCHURE,
}


def advance_bucket(current: FlowBucket) -> FlowBucket:
    try:
        idx = FLOW_ORDER.index(current)
    except ValueError:
        return FlowBucket.INTRODUCTION
    if idx >= len(FLOW_ORDER) - 1:
        return FlowBucket.CLOSING_SUMMARY
    return FLOW_ORDER[idx + 1]


def transition_to(session: SessionState, target: FlowBucket, reason: str) -> None:
    if session.flow_bucket == target:
        return
    previous = session.flow_bucket
    session.previous_bucket = previous
    session.flow_bucket = target
    logger.info(
        "state_transition session=%s %s -> %s reason=%s",
        session.session_id,
        previous.value,
        target.value,
        reason,
    )


def apply_intent_transition(session: SessionState, intent: Intent) -> None:
    """Move session bucket based on classified intent."""
    if intent == Intent.HUMAN_HANDOFF:
        return

    if intent in EDUCATION_INTENTS:
        if session.flow_bucket == FlowBucket.INTRODUCTION:
            transition_to(session, FlowBucket.EDUCATION, intent.value)
        return

    if intent in NEXT_STEPS_INTENTS:
        transition_to(session, FlowBucket.NEXT_STEPS, intent.value)
        return

    if intent == Intent.AFFIRM and session.flow_bucket != FlowBucket.CLOSING_SUMMARY:
        target = advance_bucket(session.flow_bucket)
        transition_to(session, target, "affirm_advance")
