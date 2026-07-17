"""Demo lead models + filter schemas for outbound calling eligibility."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from app.models.session import FlowBucket, Language


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    INTERESTED = "interested"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    NOT_INTERESTED = "not_interested"


# Lead status → opening flow bucket for the voice agent.
# NOT_INTERESTED is intentionally unmapped: those leads are never demo-callable.
STATUS_TO_BUCKET: dict[LeadStatus, FlowBucket] = {
    LeadStatus.NEW: FlowBucket.INTRODUCTION,
    LeadStatus.CONTACTED: FlowBucket.INTRODUCTION,
    LeadStatus.INTERESTED: FlowBucket.EDUCATION,
    LeadStatus.QUALIFIED: FlowBucket.NEXT_STEPS,
    LeadStatus.CONVERTED: FlowBucket.CLOSING_SUMMARY,
}


class BlockReason(str, Enum):
    DNC_LISTED = "dnc_listed"
    NO_CONSENT = "no_consent"
    INVALID_PHONE = "invalid_phone"
    UNSUPPORTED_STATUS = "unsupported_status"
    PROJECT_MISMATCH = "project_mismatch"
    LANGUAGE_MISMATCH = "language_mismatch"
    STATUS_NOT_SELECTED = "status_not_selected"
    OUTSIDE_CALL_WINDOW = "outside_call_window"


BLOCK_MESSAGES: dict[BlockReason, str] = {
    BlockReason.DNC_LISTED: "Lead is on the do-not-call list",
    BlockReason.NO_CONSENT: "Lead has not given calling consent",
    BlockReason.INVALID_PHONE: "Lead phone number is not valid E.164",
    BlockReason.UNSUPPORTED_STATUS: "Lead status is not callable in the demo flow",
    BlockReason.PROJECT_MISMATCH: "Lead is interested in a different project",
    BlockReason.LANGUAGE_MISMATCH: "Lead prefers a different language",
    BlockReason.STATUS_NOT_SELECTED: "Lead status is outside the selected statuses",
    BlockReason.OUTSIDE_CALL_WINDOW: "Current time is outside the lead's call window",
}


class Lead(BaseModel):
    lead_id: str
    name: str
    phone: str
    project_id: str
    language: Language = Language.EN
    status: LeadStatus = LeadStatus.NEW
    consent: bool = False
    dnc: bool = False
    # Local-hour calling window [start, end) — demo-simple timing eligibility.
    call_window_start: int = Field(default=9, ge=0, le=23)
    call_window_end: int = Field(default=21, ge=1, le=24)
    notes: str | None = None


class LeadFilterRequest(BaseModel):
    project_id: str | None = None
    language: Language | None = None
    statuses: list[LeadStatus] | None = None
    require_consent: bool = True
    exclude_dnc: bool = True
    respect_call_window: bool = True
    # Demo/testing override; defaults to the server's local hour when omitted.
    current_hour: int | None = Field(default=None, ge=0, le=23)


class FilterReason(BaseModel):
    code: BlockReason
    message: str


class EligibleLead(BaseModel):
    lead: Lead
    bucket: FlowBucket


class BlockedLead(BaseModel):
    lead: Lead
    reasons: list[FilterReason]


class LeadFilterResult(BaseModel):
    total: int
    passed: int
    blocked_count: int
    eligible: list[EligibleLead] = Field(default_factory=list)
    blocked: list[BlockedLead] = Field(default_factory=list)
    filters_applied: LeadFilterRequest
