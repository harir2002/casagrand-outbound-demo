"""Unit tests for demo lead filtering, block reasons, and bucket mapping."""

from __future__ import annotations

import pytest

from app.data.demo_leads import get_lead, list_leads
from app.models.lead import (
    BlockReason,
    Lead,
    LeadFilterRequest,
    LeadStatus,
)
from app.models.session import FlowBucket, Language
from app.services.lead_filter import (
    LeadBlockedError,
    evaluate_lead,
    filter_leads,
    map_status_to_bucket,
    require_callable_lead,
)


def _lead(**overrides) -> Lead:
    base = dict(
        lead_id="lead-test",
        name="Test Lead",
        phone="+919876543210",
        project_id="highcity",
        language=Language.EN,
        status=LeadStatus.INTERESTED,
        consent=True,
        dnc=False,
    )
    base.update(overrides)
    return Lead(**base)


def _codes(reasons) -> set[BlockReason]:
    return {r.code for r in reasons}


DEFAULT = LeadFilterRequest()


# ---------------------------------------------------------------- bucket map

def test_bucket_mapping_per_status():
    assert map_status_to_bucket(LeadStatus.NEW) == FlowBucket.INTRODUCTION
    assert map_status_to_bucket(LeadStatus.CONTACTED) == FlowBucket.INTRODUCTION
    assert map_status_to_bucket(LeadStatus.INTERESTED) == FlowBucket.EDUCATION
    assert map_status_to_bucket(LeadStatus.QUALIFIED) == FlowBucket.NEXT_STEPS
    assert map_status_to_bucket(LeadStatus.CONVERTED) == FlowBucket.CLOSING_SUMMARY
    assert map_status_to_bucket(LeadStatus.NOT_INTERESTED) is None


# ---------------------------------------------------------------- safety blocks

def test_dnc_lead_is_blocked():
    reasons = evaluate_lead(_lead(dnc=True), DEFAULT, current_hour=10)
    assert BlockReason.DNC_LISTED in _codes(reasons)


def test_dnc_allowed_when_filter_disabled():
    filters = LeadFilterRequest(exclude_dnc=False)
    reasons = evaluate_lead(_lead(dnc=True), filters, current_hour=10)
    assert BlockReason.DNC_LISTED not in _codes(reasons)


def test_missing_consent_is_blocked():
    reasons = evaluate_lead(_lead(consent=False), DEFAULT, current_hour=10)
    assert BlockReason.NO_CONSENT in _codes(reasons)


def test_invalid_phone_is_blocked():
    reasons = evaluate_lead(_lead(phone="98765"), DEFAULT, current_hour=10)
    assert BlockReason.INVALID_PHONE in _codes(reasons)


def test_unsupported_status_is_blocked():
    reasons = evaluate_lead(
        _lead(status=LeadStatus.NOT_INTERESTED), DEFAULT, current_hour=10
    )
    assert BlockReason.UNSUPPORTED_STATUS in _codes(reasons)


# ---------------------------------------------------------------- selection filters

def test_project_filter():
    filters = LeadFilterRequest(project_id="mercury")
    reasons = evaluate_lead(_lead(project_id="highcity"), filters, current_hour=10)
    assert BlockReason.PROJECT_MISMATCH in _codes(reasons)
    assert not evaluate_lead(_lead(project_id="mercury"), filters, current_hour=10)


def test_language_filter():
    filters = LeadFilterRequest(language=Language.TA)
    reasons = evaluate_lead(_lead(language=Language.EN), filters, current_hour=10)
    assert BlockReason.LANGUAGE_MISMATCH in _codes(reasons)
    assert not evaluate_lead(_lead(language=Language.TA), filters, current_hour=10)


def test_status_selection_filter():
    filters = LeadFilterRequest(statuses=[LeadStatus.QUALIFIED])
    reasons = evaluate_lead(
        _lead(status=LeadStatus.INTERESTED), filters, current_hour=10
    )
    assert BlockReason.STATUS_NOT_SELECTED in _codes(reasons)
    assert not evaluate_lead(
        _lead(status=LeadStatus.QUALIFIED), filters, current_hour=10
    )


# ---------------------------------------------------------------- timing window

def test_call_window_blocks_outside_hours():
    lead = _lead(call_window_start=18, call_window_end=21)
    assert BlockReason.OUTSIDE_CALL_WINDOW in _codes(
        evaluate_lead(lead, DEFAULT, current_hour=10)
    )
    assert not evaluate_lead(lead, DEFAULT, current_hour=19)


def test_call_window_wraps_midnight():
    lead = _lead(call_window_start=21, call_window_end=2)
    assert not evaluate_lead(lead, DEFAULT, current_hour=23)
    assert not evaluate_lead(lead, DEFAULT, current_hour=1)
    assert BlockReason.OUTSIDE_CALL_WINDOW in _codes(
        evaluate_lead(lead, DEFAULT, current_hour=12)
    )


def test_call_window_ignored_when_disabled():
    filters = LeadFilterRequest(respect_call_window=False)
    lead = _lead(call_window_start=18, call_window_end=21)
    assert not evaluate_lead(lead, filters, current_hour=10)


# ---------------------------------------------------------------- filter_leads

def test_filter_leads_on_seed_list_counts_and_reasons():
    result = filter_leads(list_leads(), LeadFilterRequest(current_hour=10))
    assert result.total == 9
    assert result.passed == 4
    assert result.blocked_count == 5

    eligible_ids = {e.lead.lead_id for e in result.eligible}
    assert eligible_ids == {"lead-anitha", "lead-rajesh", "lead-meena", "lead-suresh"}

    blocked_by_id = {b.lead.lead_id: _codes(b.reasons) for b in result.blocked}
    assert BlockReason.DNC_LISTED in blocked_by_id["lead-priya"]
    assert BlockReason.NO_CONSENT in blocked_by_id["lead-karthik"]
    assert BlockReason.INVALID_PHONE in blocked_by_id["lead-divya"]
    assert BlockReason.UNSUPPORTED_STATUS in blocked_by_id["lead-vikram"]
    assert BlockReason.OUTSIDE_CALL_WINDOW in blocked_by_id["lead-lakshmi"]


def test_filter_leads_maps_buckets():
    result = filter_leads(list_leads(), LeadFilterRequest(current_hour=10))
    buckets = {e.lead.lead_id: e.bucket for e in result.eligible}
    assert buckets["lead-rajesh"] == FlowBucket.INTRODUCTION
    assert buckets["lead-anitha"] == FlowBucket.EDUCATION
    assert buckets["lead-meena"] == FlowBucket.NEXT_STEPS
    assert buckets["lead-suresh"] == FlowBucket.CLOSING_SUMMARY


def test_filter_leads_project_and_language_combined():
    filters = LeadFilterRequest(
        project_id="highcity", language=Language.EN, current_hour=10
    )
    result = filter_leads(list_leads(), filters)
    assert {e.lead.lead_id for e in result.eligible} == {"lead-anitha"}


# ---------------------------------------------------------------- call-time gate

def test_require_callable_lead_passes_for_eligible():
    eligible = require_callable_lead(get_lead("lead-anitha"), current_hour=10)
    assert eligible.bucket == FlowBucket.EDUCATION


def test_require_callable_lead_blocks_dnc():
    with pytest.raises(LeadBlockedError) as exc_info:
        require_callable_lead(get_lead("lead-priya"), current_hour=10)
    assert BlockReason.DNC_LISTED in _codes(exc_info.value.reasons)
    assert "do-not-call" in str(exc_info.value)


def test_require_callable_lead_blocks_no_consent():
    with pytest.raises(LeadBlockedError) as exc_info:
        require_callable_lead(get_lead("lead-karthik"), current_hour=10)
    assert BlockReason.NO_CONSENT in _codes(exc_info.value.reasons)


def test_require_callable_lead_blocks_outside_window():
    with pytest.raises(LeadBlockedError) as exc_info:
        require_callable_lead(get_lead("lead-lakshmi"), current_hour=10)
    assert BlockReason.OUTSIDE_CALL_WINDOW in _codes(exc_info.value.reasons)
    # Same lead passes inside its evening window
    assert require_callable_lead(get_lead("lead-lakshmi"), current_hour=19)
