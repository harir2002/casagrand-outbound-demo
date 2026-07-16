from app.models.session import FlowBucket, Intent, SessionState
from app.services.state_machine import advance_bucket, apply_intent_transition, transition_to


def test_advance_bucket_order():
    assert advance_bucket(FlowBucket.INTRODUCTION) == FlowBucket.EDUCATION
    assert advance_bucket(FlowBucket.EDUCATION) == FlowBucket.NEXT_STEPS
    assert advance_bucket(FlowBucket.NEXT_STEPS) == FlowBucket.CLOSING_SUMMARY
    assert advance_bucket(FlowBucket.CLOSING_SUMMARY) == FlowBucket.CLOSING_SUMMARY


def test_education_intent_moves_from_introduction():
    session = SessionState(project_id="highcity")
    apply_intent_transition(session, Intent.PRICING)
    assert session.flow_bucket == FlowBucket.EDUCATION
    assert session.previous_bucket == FlowBucket.INTRODUCTION


def test_site_visit_moves_to_next_steps():
    session = SessionState(project_id="highcity", flow_bucket=FlowBucket.EDUCATION)
    apply_intent_transition(session, Intent.SITE_VISIT)
    assert session.flow_bucket == FlowBucket.NEXT_STEPS


def test_handoff_does_not_change_bucket():
    session = SessionState(project_id="highcity", flow_bucket=FlowBucket.EDUCATION)
    apply_intent_transition(session, Intent.HUMAN_HANDOFF)
    assert session.flow_bucket == FlowBucket.EDUCATION


def test_transition_to_logs_previous():
    session = SessionState(project_id="mercury")
    transition_to(session, FlowBucket.CLOSING_SUMMARY, "test")
    assert session.flow_bucket == FlowBucket.CLOSING_SUMMARY
    assert session.previous_bucket == FlowBucket.INTRODUCTION
