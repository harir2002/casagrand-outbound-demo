"""Lead eligibility filtering applied before any Twilio outbound call."""

from __future__ import annotations

from datetime import datetime

from app.core.logging import get_logger
from app.integrations.twilio.schemas import normalize_e164
from app.models.lead import (
    BLOCK_MESSAGES,
    BlockedLead,
    BlockReason,
    EligibleLead,
    FilterReason,
    Lead,
    LeadFilterRequest,
    LeadFilterResult,
    LeadStatus,
    STATUS_TO_BUCKET,
)
from app.models.session import FlowBucket

logger = get_logger(__name__)


class LeadBlockedError(Exception):
    """Raised when an outbound call targets a lead that fails eligibility."""

    def __init__(self, lead_id: str, reasons: list[FilterReason]) -> None:
        self.lead_id = lead_id
        self.reasons = reasons
        summary = "; ".join(r.message for r in reasons)
        super().__init__(f"Lead {lead_id} is not callable: {summary}")


def _reason(code: BlockReason) -> FilterReason:
    return FilterReason(code=code, message=BLOCK_MESSAGES[code])


def map_status_to_bucket(status: LeadStatus) -> FlowBucket | None:
    return STATUS_TO_BUCKET.get(status)


def _in_call_window(lead: Lead, hour: int) -> bool:
    start, end = lead.call_window_start, lead.call_window_end
    if start == end:
        return False
    if start < end:
        return start <= hour < end
    # Window wraps past midnight (e.g. 21 → 2)
    return hour >= start or hour < end


def evaluate_lead(
    lead: Lead,
    filters: LeadFilterRequest,
    *,
    current_hour: int | None = None,
) -> list[FilterReason]:
    """All block reasons for one lead under the given filters (empty = eligible)."""
    reasons: list[FilterReason] = []

    # Safety blocks
    if filters.exclude_dnc and lead.dnc:
        reasons.append(_reason(BlockReason.DNC_LISTED))
    if filters.require_consent and not lead.consent:
        reasons.append(_reason(BlockReason.NO_CONSENT))
    if normalize_e164(lead.phone) is None:
        reasons.append(_reason(BlockReason.INVALID_PHONE))
    if map_status_to_bucket(lead.status) is None:
        reasons.append(_reason(BlockReason.UNSUPPORTED_STATUS))

    # Selection filters
    if filters.project_id and lead.project_id != filters.project_id.lower():
        reasons.append(_reason(BlockReason.PROJECT_MISMATCH))
    if filters.language and lead.language != filters.language:
        reasons.append(_reason(BlockReason.LANGUAGE_MISMATCH))
    if filters.statuses and lead.status not in filters.statuses:
        reasons.append(_reason(BlockReason.STATUS_NOT_SELECTED))

    # Timing window
    if filters.respect_call_window:
        hour = (
            current_hour
            if current_hour is not None
            else filters.current_hour
            if filters.current_hour is not None
            else datetime.now().hour
        )
        if not _in_call_window(lead, hour):
            reasons.append(_reason(BlockReason.OUTSIDE_CALL_WINDOW))

    return reasons


def filter_leads(
    leads: list[Lead],
    filters: LeadFilterRequest,
    *,
    current_hour: int | None = None,
) -> LeadFilterResult:
    eligible: list[EligibleLead] = []
    blocked: list[BlockedLead] = []
    for lead in leads:
        reasons = evaluate_lead(lead, filters, current_hour=current_hour)
        if reasons:
            blocked.append(BlockedLead(lead=lead, reasons=reasons))
        else:
            bucket = map_status_to_bucket(lead.status)
            assert bucket is not None  # unsupported statuses are already blocked
            eligible.append(EligibleLead(lead=lead, bucket=bucket))

    result = LeadFilterResult(
        total=len(leads),
        passed=len(eligible),
        blocked_count=len(blocked),
        eligible=eligible,
        blocked=blocked,
        filters_applied=filters,
    )
    logger.info(
        "lead_filter total=%s passed=%s blocked=%s project=%s language=%s",
        result.total,
        result.passed,
        result.blocked_count,
        filters.project_id or "*",
        filters.language.value if filters.language else "*",
    )
    return result


def require_callable_lead(
    lead: Lead,
    *,
    current_hour: int | None = None,
) -> EligibleLead:
    """Strict safety gate used at call time: DNC, consent, phone, status, window.

    Selection filters (project/language/status choice) are UI concerns and are
    not re-applied here — safety and timing rules always are.
    """
    strict = LeadFilterRequest(
        require_consent=True,
        exclude_dnc=True,
        respect_call_window=True,
    )
    reasons = evaluate_lead(lead, strict, current_hour=current_hour)
    if reasons:
        raise LeadBlockedError(lead.lead_id, reasons)
    bucket = map_status_to_bucket(lead.status)
    assert bucket is not None
    return EligibleLead(lead=lead, bucket=bucket)
