"""Seeded demo lead list — deliberately covers every filter/block case."""

from __future__ import annotations

from app.models.lead import Lead, LeadStatus
from app.models.session import Language

_DEMO_LEADS: list[Lead] = [
    Lead(
        lead_id="lead-anitha",
        name="Anitha Raman",
        phone="+919876543210",
        project_id="highcity",
        language=Language.EN,
        status=LeadStatus.INTERESTED,
        consent=True,
        notes="Asked for pricing on 3 BHK",
    ),
    Lead(
        lead_id="lead-rajesh",
        name="Rajesh Kumar",
        phone="+919812345678",
        project_id="highcity",
        language=Language.TA,
        status=LeadStatus.NEW,
        consent=True,
        notes="Website enquiry, not yet contacted",
    ),
    Lead(
        lead_id="lead-meena",
        name="Meena Srinivasan",
        phone="+919845612378",
        project_id="avenuepark",
        language=Language.TANGLISH,
        status=LeadStatus.QUALIFIED,
        consent=True,
        notes="Wants a weekend site visit",
    ),
    Lead(
        lead_id="lead-suresh",
        name="Suresh Babu",
        phone="+919867453120",
        project_id="mercury",
        language=Language.EN,
        status=LeadStatus.CONVERTED,
        consent=True,
        notes="Booking done, closing summary pending",
    ),
    Lead(
        lead_id="lead-priya",
        name="Priya Venkatesh",
        phone="+919833221100",
        project_id="highcity",
        language=Language.EN,
        status=LeadStatus.INTERESTED,
        consent=True,
        dnc=True,
        notes="Requested do-not-call",
    ),
    Lead(
        lead_id="lead-karthik",
        name="Karthik Anand",
        phone="+919877665544",
        project_id="avenuepark",
        language=Language.TA,
        status=LeadStatus.NEW,
        consent=False,
        notes="No consent recorded yet",
    ),
    Lead(
        lead_id="lead-divya",
        name="Divya Prakash",
        phone="98765",  # deliberately invalid (missing +country code)
        project_id="mercury",
        language=Language.EN,
        status=LeadStatus.QUALIFIED,
        consent=True,
        notes="Phone captured incorrectly",
    ),
    Lead(
        lead_id="lead-vikram",
        name="Vikram Shetty",
        phone="+919811223344",
        project_id="highcity",
        language=Language.EN,
        status=LeadStatus.NOT_INTERESTED,
        consent=True,
        notes="Declined after first call",
    ),
    Lead(
        lead_id="lead-lakshmi",
        name="Lakshmi Narayan",
        phone="+919855443322",
        project_id="avenuepark",
        language=Language.EN,
        status=LeadStatus.CONTACTED,
        consent=True,
        call_window_start=18,
        call_window_end=21,
        notes="Only reachable in the evening",
    ),
]


def list_leads() -> list[Lead]:
    return [lead.model_copy(deep=True) for lead in _DEMO_LEADS]


def get_lead(lead_id: str) -> Lead | None:
    for lead in _DEMO_LEADS:
        if lead.lead_id == lead_id:
            return lead.model_copy(deep=True)
    return None
