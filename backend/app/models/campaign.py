"""Demo campaign models: filtered-lead dial runs with per-lead tracking."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.lead import FilterReason, LeadFilterRequest, LeadStatus
from app.models.session import FlowBucket, Language


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LeadCallState(str, Enum):
    PENDING = "pending"
    DIALING = "dialing"
    CONNECTED = "connected"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


TERMINAL_LEAD_STATES = {
    LeadCallState.COMPLETED,
    LeadCallState.BLOCKED,
    LeadCallState.FAILED,
}


class CampaignLeadResult(BaseModel):
    lead_id: str
    name: str
    phone: str
    project_id: str
    language: Language
    lead_status: LeadStatus
    bucket: FlowBucket | None = None
    state: LeadCallState = LeadCallState.PENDING
    call_sid: str | None = None
    call_status: str | None = None
    session_id: str | None = None
    duration: str | None = None
    reasons: list[FilterReason] = Field(default_factory=list)
    error: str | None = None
    # False when the lead was already blocked by the filter snapshot (vs. the
    # call-time safety gate blocking it mid-run).
    eligible_at_creation: bool = True


class CampaignSummary(BaseModel):
    total: int
    eligible: int
    blocked: int
    states: dict[str, int] = Field(default_factory=dict)
    buckets: dict[str, int] = Field(default_factory=dict)
    done: bool = False


class Campaign(BaseModel):
    campaign_id: str = Field(default_factory=lambda: f"cmp-{uuid4().hex[:8]}")
    status: CampaignStatus = CampaignStatus.DRAFT
    filters: LeadFilterRequest
    leads: list[CampaignLeadResult] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    finished_at: datetime | None = None


class CampaignCreateRequest(BaseModel):
    filters: LeadFilterRequest = Field(default_factory=LeadFilterRequest)


class CampaignStartRequest(BaseModel):
    # Dial one lead at a time; wait for the current call to end before the next.
    wait_for_terminal: bool = True
    max_wait_s: float = Field(default=120.0, ge=1.0, le=900.0)
    poll_interval_s: float = Field(default=2.0, ge=0.1, le=30.0)


class CampaignView(BaseModel):
    campaign: Campaign
    summary: CampaignSummary
