"""Demo campaign orchestration: filter snapshot → sequential dial → tracking.

Every dial goes through TwilioCallService.start_outbound_call(lead_id=...),
so the lead safety gate (DNC / consent / phone / status / call window) is
re-applied per call — the campaign layer never bypasses it.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger
from app.data.demo_leads import list_leads
from app.integrations.twilio import call_registry
from app.integrations.twilio.schemas import OutboundCallRequest, OutboundCallResponse
from app.models.campaign import (
    Campaign,
    CampaignLeadResult,
    CampaignStatus,
    CampaignSummary,
    CampaignView,
    LeadCallState,
    TERMINAL_LEAD_STATES,
)
from app.models.lead import LeadFilterRequest
from app.services.lead_filter import LeadBlockedError, filter_leads

logger = get_logger(__name__)

Dialer = Callable[[str], Awaitable[OutboundCallResponse]]
StatusLookup = Callable[[str], dict[str, Any] | None]

_campaigns: dict[str, Campaign] = {}

# Twilio call statuses → campaign lead states
_STATUS_TO_STATE: dict[str, LeadCallState] = {
    "queued": LeadCallState.DIALING,
    "initiated": LeadCallState.DIALING,
    "ringing": LeadCallState.DIALING,
    "in-progress": LeadCallState.CONNECTED,
    "answered": LeadCallState.CONNECTED,
    "completed": LeadCallState.COMPLETED,
    "busy": LeadCallState.FAILED,
    "failed": LeadCallState.FAILED,
    "no-answer": LeadCallState.FAILED,
    "canceled": LeadCallState.FAILED,
}


def map_call_status_to_state(status: str | None) -> LeadCallState:
    return _STATUS_TO_STATE.get((status or "").lower(), LeadCallState.DIALING)


async def _default_dialer(lead_id: str) -> OutboundCallResponse:
    # Imported lazily so tests can monkeypatch TwilioCallService cleanly.
    from app.integrations.twilio.service import TwilioCallService

    service = TwilioCallService()
    return await service.start_outbound_call(OutboundCallRequest(lead_id=lead_id))


def create_campaign(filters: LeadFilterRequest) -> Campaign:
    """Snapshot the filtered lead list into a trackable campaign."""
    result = filter_leads(list_leads(), filters)
    leads: list[CampaignLeadResult] = []
    for entry in result.eligible:
        leads.append(
            CampaignLeadResult(
                lead_id=entry.lead.lead_id,
                name=entry.lead.name,
                phone=entry.lead.phone,
                project_id=entry.lead.project_id,
                language=entry.lead.language,
                lead_status=entry.lead.status,
                bucket=entry.bucket,
                state=LeadCallState.PENDING,
            )
        )
    for blocked in result.blocked:
        leads.append(
            CampaignLeadResult(
                lead_id=blocked.lead.lead_id,
                name=blocked.lead.name,
                phone=blocked.lead.phone,
                project_id=blocked.lead.project_id,
                language=blocked.lead.language,
                lead_status=blocked.lead.status,
                state=LeadCallState.BLOCKED,
                reasons=blocked.reasons,
                eligible_at_creation=False,
            )
        )

    campaign = Campaign(filters=filters, leads=leads)
    _campaigns[campaign.campaign_id] = campaign
    logger.info(
        "campaign_created id=%s total=%s eligible=%s blocked=%s",
        campaign.campaign_id,
        result.total,
        result.passed,
        result.blocked_count,
    )
    return campaign


def get_campaign(campaign_id: str) -> Campaign | None:
    return _campaigns.get(campaign_id)


def list_campaigns() -> list[Campaign]:
    return sorted(_campaigns.values(), key=lambda c: c.created_at, reverse=True)


def cancel_campaign(campaign_id: str) -> Campaign | None:
    campaign = _campaigns.get(campaign_id)
    if campaign is None:
        return None
    if campaign.status in {CampaignStatus.DRAFT, CampaignStatus.RUNNING}:
        campaign.status = CampaignStatus.CANCELLED
        campaign.finished_at = datetime.now(timezone.utc)
        logger.info("campaign_cancelled id=%s", campaign_id)
    return campaign


def clear_campaigns() -> None:
    _campaigns.clear()


def _update_from_registry(
    result: CampaignLeadResult,
    status_lookup: StatusLookup,
) -> None:
    if not result.call_sid:
        return
    entry = status_lookup(result.call_sid)
    if not entry:
        return
    status = entry.get("status")
    if status:
        result.call_status = str(status)
        result.state = map_call_status_to_state(str(status))
    if entry.get("duration"):
        result.duration = str(entry["duration"])


def refresh_campaign(
    campaign: Campaign,
    status_lookup: StatusLookup | None = None,
) -> Campaign:
    """Pull latest call statuses (fed by Twilio status callbacks) into lead states."""
    lookup = status_lookup or call_registry.get_call
    for result in campaign.leads:
        if result.state in (LeadCallState.DIALING, LeadCallState.CONNECTED):
            _update_from_registry(result, lookup)
    return campaign


def summarize_campaign(campaign: Campaign) -> CampaignSummary:
    states: dict[str, int] = {}
    buckets: dict[str, int] = {}
    eligible = 0
    for result in campaign.leads:
        states[result.state.value] = states.get(result.state.value, 0) + 1
        if result.bucket is not None:
            buckets[result.bucket.value] = buckets.get(result.bucket.value, 0) + 1
        if result.eligible_at_creation:
            eligible += 1
    return CampaignSummary(
        total=len(campaign.leads),
        eligible=eligible,
        blocked=states.get(LeadCallState.BLOCKED.value, 0),
        states=states,
        buckets=buckets,
        done=campaign.status in {CampaignStatus.COMPLETED, CampaignStatus.CANCELLED},
    )


def campaign_view(campaign: Campaign) -> CampaignView:
    return CampaignView(campaign=campaign, summary=summarize_campaign(campaign))


async def run_campaign(
    campaign_id: str,
    *,
    wait_for_terminal: bool = True,
    max_wait_s: float = 120.0,
    poll_interval_s: float = 2.0,
    dialer: Dialer | None = None,
    status_lookup: StatusLookup | None = None,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> Campaign:
    """Dial pending leads one at a time, tracking per-lead outcomes."""
    campaign = _campaigns.get(campaign_id)
    if campaign is None:
        raise LookupError(f"Unknown campaign: {campaign_id}")
    if campaign.status == CampaignStatus.RUNNING:
        return campaign

    dial = dialer or _default_dialer
    lookup = status_lookup or call_registry.get_call

    campaign.status = CampaignStatus.RUNNING
    campaign.started_at = datetime.now(timezone.utc)
    logger.info("campaign_started id=%s", campaign_id)

    for result in campaign.leads:
        if campaign.status == CampaignStatus.CANCELLED:
            break
        if result.state != LeadCallState.PENDING:
            continue

        result.state = LeadCallState.DIALING
        try:
            response = await dial(result.lead_id)
        except LeadBlockedError as exc:
            result.state = LeadCallState.BLOCKED
            result.reasons = exc.reasons
            logger.info("campaign_lead_blocked id=%s lead=%s", campaign_id, result.lead_id)
            continue
        except Exception as exc:  # noqa: BLE001 — one bad dial must not kill the run
            result.state = LeadCallState.FAILED
            result.error = str(exc)
            logger.warning(
                "campaign_lead_failed id=%s lead=%s error=%s",
                campaign_id,
                result.lead_id,
                exc,
            )
            continue

        result.call_sid = response.call_sid
        result.session_id = response.session_id
        result.call_status = response.status
        result.state = map_call_status_to_state(response.status)
        logger.info(
            "campaign_lead_dialed id=%s lead=%s sid=%s",
            campaign_id,
            result.lead_id,
            response.call_sid,
        )

        if wait_for_terminal and result.call_sid:
            deadline = time.monotonic() + max_wait_s
            while time.monotonic() < deadline:
                if campaign.status == CampaignStatus.CANCELLED:
                    break
                _update_from_registry(result, lookup)
                if result.state in TERMINAL_LEAD_STATES:
                    break
                await sleep(poll_interval_s)

    if campaign.status != CampaignStatus.CANCELLED:
        campaign.status = CampaignStatus.COMPLETED
    campaign.finished_at = datetime.now(timezone.utc)
    logger.info(
        "campaign_finished id=%s status=%s summary=%s",
        campaign_id,
        campaign.status.value,
        summarize_campaign(campaign).states,
    )
    return campaign
