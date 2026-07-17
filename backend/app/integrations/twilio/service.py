"""Outbound Twilio call initiation service."""

from __future__ import annotations

import time
from typing import Any

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.integrations.twilio import call_registry
from app.integrations.twilio.client import TwilioRestClient, build_query_url
from app.integrations.twilio.config import TwilioConfig, require_twilio_ready
from app.data.demo_leads import get_lead
from app.integrations.twilio.schemas import (
    OutboundCallRequest,
    OutboundCallResponse,
    normalize_e164,
)
from app.integrations.twilio.twiml import build_media_stream_twiml
from app.models.lead import EligibleLead
from app.models.session import CreateSessionRequest, Language
from app.services import call_service
from app.services.lead_filter import require_callable_lead
from app.services.session_store import store
from app.services.state_machine import transition_to

logger = get_logger(__name__)


class TwilioCallService:
    def __init__(
        self,
        config: TwilioConfig | None = None,
        settings: Settings | None = None,
        client: TwilioRestClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.config = config or require_twilio_ready(self.settings)
        self.client = client or TwilioRestClient(self.config)

    async def start_outbound_call(self, request: OutboundCallRequest) -> OutboundCallResponse:
        started = time.perf_counter()
        project_id = request.project_id or self.settings.default_project
        language = request.language or Language(self.settings.default_language)

        # Lead-driven calls: resolve the demo lead and re-run the safety gate
        # (DNC / consent / phone / status / call window) before any dial.
        eligible: EligibleLead | None = None
        to = request.to
        if request.lead_id:
            lead = get_lead(request.lead_id)
            if lead is None:
                raise LookupError(f"Unknown lead_id: {request.lead_id}")
            eligible = require_callable_lead(lead)
            to = normalize_e164(lead.phone) or lead.phone
            project_id = lead.project_id
            language = lead.language
        assert to is not None  # schema enforces to or lead_id

        if request.session_id:
            session_result = call_service.get_session(request.session_id)
            session_id = session_result.session.session_id
            project_id = session_result.session.project_id
            language = session_result.session.language
        else:
            session_result = call_service.create_session(
                CreateSessionRequest(project_id=project_id, language=language)
            )
            session_id = session_result.session.session_id
            if eligible is not None and eligible.bucket != session_result.session.flow_bucket:
                # Start the voice agent in the bucket matching the lead's status.
                transition_to(
                    session_result.session,
                    eligible.bucket,
                    f"lead_status:{eligible.lead.status.value}",
                )
                store.save(session_result.session)

        # CRM context: remember who we are calling so summaries/handoffs carry it.
        customer_name = request.customer_name or (eligible.lead.name if eligible else None)
        if customer_name and session_result.session.memory.caller_name != customer_name:
            session_result.session.memory.caller_name = customer_name
            store.save(session_result.session)

        twiml_url: str | None = request.twiml_url
        inline_twiml: str | None = request.twiml
        used_inline = False

        if not twiml_url and not inline_twiml:
            twiml_url = build_query_url(
                self.config.voice_webhook_url,
                {
                    "session_id": session_id,
                    "project_id": project_id,
                    "language": language.value,
                },
            )

        if inline_twiml and not request.twiml_url:
            used_inline = True
            payload = await self.client.create_call(
                to=to,
                twiml=inline_twiml,
                status_callback=self.config.status_callback_url,
            )
        else:
            payload = await self.client.create_call(
                to=to,
                url=twiml_url,
                status_callback=self.config.status_callback_url,
            )

        call_sid = str(payload.get("sid") or "")
        status = str(payload.get("status") or "queued")
        initiate_ms = round((time.perf_counter() - started) * 1000, 2)
        if call_sid:
            call_registry.record_call(
                call_sid,
                to=to,
                from_number=self.config.from_number,
                session_id=session_id,
                status=status,
            )
        logger.info(
            "twilio_outbound_call sid=%s to=%s session=%s status=%s lead=%s initiate_ms=%s",
            call_sid,
            to,
            session_id,
            status,
            request.lead_id or "-",
            initiate_ms,
        )
        provider_meta: dict[str, Any] = {
            "twilio_account_sid": self.config.account_sid[:6] + "…",
            "inline_twiml": used_inline,
            "raw_status": status,
            "direction": payload.get("direction"),
            "timings": {"initiate_ms": initiate_ms},
        }
        if customer_name:
            provider_meta["customer_name"] = customer_name
        if eligible is not None:
            provider_meta["lead"] = {
                "lead_id": eligible.lead.lead_id,
                "name": eligible.lead.name,
                "status": eligible.lead.status.value,
                "bucket": eligible.bucket.value,
            }
        return OutboundCallResponse(
            call_sid=call_sid,
            to=to,
            from_number=self.config.from_number,
            status=status,
            session_id=session_id,
            project_id=project_id,
            language=language.value,
            transport="twilio_voice",
            media_stream="websocket",
            twiml_url=None if used_inline else twiml_url,
            provider_meta=provider_meta,
        )

    def build_default_stream_twiml(
        self,
        *,
        session_id: str,
        project_id: str,
        language: str,
    ) -> str:
        return build_media_stream_twiml(
            self.config.media_stream_wss_url,
            parameters={
                "session_id": session_id,
                "project_id": project_id,
                "language": language,
            },
            status_callback=self.config.status_callback_url,
        )


def build_outbound_call_body_for_tests(
    *,
    to: str,
    from_number: str,
    url: str | None = None,
    twiml: str | None = None,
) -> dict[str, Any]:
    """Pure helper used by unit tests to assert REST form fields."""
    data: dict[str, Any] = {"To": to, "From": from_number}
    if url:
        data["Url"] = url
        data["Method"] = "POST"
    if twiml:
        data["Twiml"] = twiml
    return data
