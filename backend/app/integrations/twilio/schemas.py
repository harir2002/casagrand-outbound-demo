"""Pydantic models for Twilio HTTP APIs."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.session import Language

_E164_RE = re.compile(r"^\+[1-9]\d{7,14}$")


def normalize_e164(raw: str) -> str | None:
    """Strip separators and validate E.164. Returns normalized number or None."""
    cleaned = re.sub(r"[\s\-().]", "", (raw or "").strip())
    if not cleaned:
        return None
    return cleaned if _E164_RE.fullmatch(cleaned) else None


class OutboundCallRequest(BaseModel):
    to: str | None = Field(
        default=None, description="E.164 destination number (or provide lead_id)"
    )
    lead_id: str | None = Field(
        default=None,
        description="Demo lead to call; eligibility is re-checked server-side",
    )
    customer_name: str | None = Field(
        default=None,
        max_length=120,
        description="Customer name for CRM context and personalization",
    )

    @field_validator("customer_name")
    @classmethod
    def _clean_name(cls, value: str | None) -> str | None:
        cleaned = (value or "").strip()
        return cleaned or None

    @field_validator("to")
    @classmethod
    def _validate_to(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = normalize_e164(value)
        if not normalized:
            raise ValueError(
                "Destination must be E.164 format, e.g. +919876543210 "
                "(+ country code, 8-15 digits)"
            )
        return normalized

    @model_validator(mode="after")
    def _require_destination(self) -> "OutboundCallRequest":
        if not self.to and not self.lead_id:
            raise ValueError("Provide either 'to' (E.164 number) or 'lead_id'")
        return self
    project_id: str | None = None
    language: Language | None = None
    session_id: str | None = Field(
        default=None,
        description="Reuse an existing demo session; otherwise a new one is created",
    )
    twiml_url: str | None = Field(
        default=None,
        description="Optional absolute TwiML webhook URL (overrides default voice webhook)",
    )
    twiml: str | None = Field(
        default=None,
        description="Optional inline TwiML (used when twiml_url is not provided)",
    )


class OutboundCallResponse(BaseModel):
    call_sid: str
    to: str
    from_number: str
    status: str
    session_id: str
    project_id: str
    language: str
    transport: str = "twilio_voice"
    media_stream: str = "websocket"
    twiml_url: str | None = None
    provider_meta: dict[str, Any] = Field(default_factory=dict)


class VoiceWebhookQuery(BaseModel):
    session_id: str | None = None
    project_id: str | None = None
    language: str | None = None
