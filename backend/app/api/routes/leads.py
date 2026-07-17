"""Demo lead list + eligibility filtering endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.data.demo_leads import list_leads
from app.models.lead import Lead, LeadFilterRequest, LeadFilterResult, LeadStatus
from app.services.lead_filter import filter_leads

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=list[Lead])
def get_leads() -> list[Lead]:
    return list_leads()


@router.get("/statuses")
def get_lead_statuses() -> list[str]:
    return [status.value for status in LeadStatus]


@router.post("/filter", response_model=LeadFilterResult)
def apply_lead_filters(filters: LeadFilterRequest) -> LeadFilterResult:
    """Apply demo eligibility filters; returns eligible leads with target buckets
    plus blocked leads with structured reasons."""
    return filter_leads(list_leads(), filters)
