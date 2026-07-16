from app.models import FlowBucket, Intent, SessionState


FLOW_ORDER: list[FlowBucket] = [
    FlowBucket.INTRODUCTION,
    FlowBucket.EDUCATION,
    FlowBucket.NEXT_STEPS,
    FlowBucket.SUMMARY,
]


def advance_bucket(current: FlowBucket) -> FlowBucket:
    try:
        idx = FLOW_ORDER.index(current)
    except ValueError:
        return FlowBucket.INTRODUCTION
    if idx >= len(FLOW_ORDER) - 1:
        return FlowBucket.SUMMARY
    return FLOW_ORDER[idx + 1]


def apply_flow_transition(session: SessionState, intent: Intent) -> None:
    """Update flow bucket based on intent and current progress."""
    if intent == Intent.HUMAN_HANDOFF:
        return

    if intent in {
        Intent.PROJECT_INFO,
        Intent.PRICING,
        Intent.LOCATION,
        Intent.AMENITIES,
        Intent.CONTEXT_SWITCH,
    }:
        if session.flow_bucket == FlowBucket.INTRODUCTION:
            session.previous_bucket = session.flow_bucket
            session.flow_bucket = FlowBucket.EDUCATION
        return

    if intent == Intent.SITE_VISIT:
        session.previous_bucket = session.flow_bucket
        session.flow_bucket = FlowBucket.NEXT_STEPS
        return

    if intent == Intent.CALLBACK:
        if session.flow_bucket in {FlowBucket.INTRODUCTION, FlowBucket.EDUCATION}:
            session.previous_bucket = session.flow_bucket
            session.flow_bucket = FlowBucket.NEXT_STEPS
        return

    if intent == Intent.AFFIRM and session.flow_bucket != FlowBucket.SUMMARY:
        session.previous_bucket = session.flow_bucket
        session.flow_bucket = advance_bucket(session.flow_bucket)
