"""Demo campaign endpoints: create from filters, start dial run, track progress."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException

from app.core.logging import get_logger
from app.models.campaign import (
    CampaignCreateRequest,
    CampaignStartRequest,
    CampaignStatus,
    CampaignView,
)
from app.services import campaign_service

logger = get_logger(__name__)
router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def _view_or_404(campaign_id: str) -> CampaignView:
    campaign = campaign_service.get_campaign(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail=f"Unknown campaign: {campaign_id}")
    campaign_service.refresh_campaign(campaign)
    return campaign_service.campaign_view(campaign)


@router.post("", response_model=CampaignView)
def create_campaign(payload: CampaignCreateRequest) -> CampaignView:
    """Snapshot the filtered demo lead list into a new campaign (no dialing yet)."""
    campaign = campaign_service.create_campaign(payload.filters)
    return campaign_service.campaign_view(campaign)


@router.get("", response_model=list[CampaignView])
def list_campaigns() -> list[CampaignView]:
    return [campaign_service.campaign_view(c) for c in campaign_service.list_campaigns()]


@router.get("/{campaign_id}", response_model=CampaignView)
def get_campaign(campaign_id: str) -> CampaignView:
    return _view_or_404(campaign_id)


@router.post("/{campaign_id}/start", response_model=CampaignView)
async def start_campaign(
    campaign_id: str, payload: CampaignStartRequest | None = None
) -> CampaignView:
    campaign = campaign_service.get_campaign(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail=f"Unknown campaign: {campaign_id}")
    if campaign.status == CampaignStatus.RUNNING:
        raise HTTPException(status_code=409, detail="Campaign is already running")
    if campaign.status in {CampaignStatus.COMPLETED, CampaignStatus.CANCELLED}:
        raise HTTPException(
            status_code=409, detail=f"Campaign already {campaign.status.value}"
        )

    options = payload or CampaignStartRequest()
    asyncio.create_task(
        campaign_service.run_campaign(
            campaign_id,
            wait_for_terminal=options.wait_for_terminal,
            max_wait_s=options.max_wait_s,
            poll_interval_s=options.poll_interval_s,
        )
    )
    # Give the runner a tick so the returned snapshot shows "running".
    await asyncio.sleep(0)
    return _view_or_404(campaign_id)


@router.post("/{campaign_id}/cancel", response_model=CampaignView)
def cancel_campaign(campaign_id: str) -> CampaignView:
    campaign = campaign_service.cancel_campaign(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail=f"Unknown campaign: {campaign_id}")
    return campaign_service.campaign_view(campaign)
