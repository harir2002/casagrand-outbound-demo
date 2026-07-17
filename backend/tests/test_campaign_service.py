"""Unit tests for campaign scheduling, per-lead tracking, and summaries."""

from __future__ import annotations

import pytest

from app.models.campaign import CampaignStatus, LeadCallState
from app.models.lead import BlockReason, FilterReason, LeadFilterRequest
from app.services import campaign_service
from app.services.campaign_service import (
    cancel_campaign,
    create_campaign,
    map_call_status_to_state,
    run_campaign,
    summarize_campaign,
)
from app.services.lead_filter import LeadBlockedError


DAY_FILTERS = LeadFilterRequest(current_hour=10)


@pytest.fixture(autouse=True)
def _clean_campaigns():
    campaign_service.clear_campaigns()
    yield
    campaign_service.clear_campaigns()


class _FakeDialer:
    """Dials succeed unless the lead_id is in `blocked` or `failing`."""

    def __init__(self, blocked=(), failing=()):
        self.blocked = set(blocked)
        self.failing = set(failing)
        self.dialed: list[str] = []

    async def __call__(self, lead_id: str):
        self.dialed.append(lead_id)
        if lead_id in self.blocked:
            raise LeadBlockedError(
                lead_id,
                [FilterReason(code=BlockReason.DNC_LISTED, message="Lead is on the do-not-call list")],
            )
        if lead_id in self.failing:
            raise RuntimeError("Twilio create call failed (401)")
        from app.integrations.twilio.schemas import OutboundCallResponse

        return OutboundCallResponse(
            call_sid=f"CA-{lead_id}",
            to="+919876543210",
            from_number="+15551234567",
            status="queued",
            session_id=f"sess-{lead_id}",
            project_id="highcity",
            language="en",
        )


def test_map_call_status_to_state():
    assert map_call_status_to_state("queued") == LeadCallState.DIALING
    assert map_call_status_to_state("ringing") == LeadCallState.DIALING
    assert map_call_status_to_state("in-progress") == LeadCallState.CONNECTED
    assert map_call_status_to_state("answered") == LeadCallState.CONNECTED
    assert map_call_status_to_state("completed") == LeadCallState.COMPLETED
    assert map_call_status_to_state("busy") == LeadCallState.FAILED
    assert map_call_status_to_state("no-answer") == LeadCallState.FAILED
    assert map_call_status_to_state(None) == LeadCallState.DIALING


def test_create_campaign_snapshots_filtered_leads():
    campaign = create_campaign(DAY_FILTERS)
    summary = summarize_campaign(campaign)
    assert summary.total == 9
    assert summary.eligible == 4
    assert summary.blocked == 5
    assert summary.buckets == {
        "introduction": 1,
        "education": 1,
        "next_steps": 1,
        "closing_summary": 1,
    }
    pending = [l for l in campaign.leads if l.state == LeadCallState.PENDING]
    assert {l.lead_id for l in pending} == {
        "lead-anitha",
        "lead-rajesh",
        "lead-meena",
        "lead-suresh",
    }
    blocked = [l for l in campaign.leads if l.state == LeadCallState.BLOCKED]
    assert all(l.reasons for l in blocked)
    assert all(not l.eligible_at_creation for l in blocked)


@pytest.mark.asyncio
async def test_run_campaign_dials_eligible_leads_in_order():
    campaign = create_campaign(DAY_FILTERS)
    dialer = _FakeDialer()
    done = await run_campaign(
        campaign.campaign_id,
        wait_for_terminal=False,
        dialer=dialer,
        status_lookup=lambda sid: None,
    )
    assert done.status == CampaignStatus.COMPLETED
    assert dialer.dialed == ["lead-anitha", "lead-rajesh", "lead-meena", "lead-suresh"]
    dialed = {l.lead_id: l for l in done.leads if l.call_sid}
    assert dialed["lead-anitha"].call_sid == "CA-lead-anitha"
    assert dialed["lead-anitha"].session_id == "sess-lead-anitha"
    assert dialed["lead-anitha"].state == LeadCallState.DIALING  # queued, no callbacks
    assert done.started_at is not None and done.finished_at is not None


@pytest.mark.asyncio
async def test_run_campaign_waits_for_terminal_status():
    campaign = create_campaign(
        LeadFilterRequest(project_id="highcity", current_hour=10)
    )
    dialer = _FakeDialer()

    # Registry stub: first lookup says in-progress, second says completed.
    lookups: dict[str, int] = {}

    def status_lookup(call_sid: str):
        count = lookups.get(call_sid, 0)
        lookups[call_sid] = count + 1
        if count == 0:
            return {"status": "in-progress"}
        return {"status": "completed", "duration": "35"}

    async def no_sleep(_seconds: float) -> None:
        return None

    done = await run_campaign(
        campaign.campaign_id,
        wait_for_terminal=True,
        max_wait_s=5,
        poll_interval_s=0.01,
        dialer=dialer,
        status_lookup=status_lookup,
        sleep=no_sleep,
    )
    completed = [l for l in done.leads if l.state == LeadCallState.COMPLETED]
    assert {l.lead_id for l in completed} == {"lead-anitha", "lead-rajesh"}
    assert all(l.call_status == "completed" for l in completed)
    assert all(l.duration == "35" for l in completed)


@pytest.mark.asyncio
async def test_run_campaign_tracks_blocked_and_failed_leads():
    campaign = create_campaign(DAY_FILTERS)
    dialer = _FakeDialer(blocked={"lead-rajesh"}, failing={"lead-meena"})
    done = await run_campaign(
        campaign.campaign_id,
        wait_for_terminal=False,
        dialer=dialer,
        status_lookup=lambda sid: None,
    )
    by_id = {l.lead_id: l for l in done.leads}
    assert by_id["lead-rajesh"].state == LeadCallState.BLOCKED
    assert by_id["lead-rajesh"].reasons[0].code == BlockReason.DNC_LISTED
    assert by_id["lead-meena"].state == LeadCallState.FAILED
    assert "401" in by_id["lead-meena"].error
    # One bad lead never stops the run
    assert by_id["lead-suresh"].call_sid == "CA-lead-suresh"
    assert done.status == CampaignStatus.COMPLETED


@pytest.mark.asyncio
async def test_cancel_stops_remaining_dials():
    campaign = create_campaign(DAY_FILTERS)

    class _CancellingDialer(_FakeDialer):
        async def __call__(self, lead_id: str):
            response = await super().__call__(lead_id)
            if len(self.dialed) == 2:
                cancel_campaign(campaign.campaign_id)
            return response

    dialer = _CancellingDialer()
    done = await run_campaign(
        campaign.campaign_id,
        wait_for_terminal=False,
        dialer=dialer,
        status_lookup=lambda sid: None,
    )
    assert done.status == CampaignStatus.CANCELLED
    assert len(dialer.dialed) == 2
    remaining = [l for l in done.leads if l.state == LeadCallState.PENDING]
    assert {l.lead_id for l in remaining} == {"lead-meena", "lead-suresh"}


def test_summary_reflects_states_after_run():
    campaign = create_campaign(DAY_FILTERS)
    # Simulate a finished run by hand
    for lead in campaign.leads:
        if lead.state == LeadCallState.PENDING:
            lead.state = LeadCallState.COMPLETED
    campaign.status = CampaignStatus.COMPLETED
    summary = summarize_campaign(campaign)
    assert summary.states["completed"] == 4
    assert summary.states["blocked"] == 5
    assert summary.done is True
