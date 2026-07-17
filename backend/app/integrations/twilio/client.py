"""Twilio Voice REST client (httpx) + request signature validation."""

from __future__ import annotations

import base64
import hashlib
import hmac
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.logging import get_logger
from app.integrations.twilio.config import TwilioConfig

logger = get_logger(__name__)

TWILIO_API_BASE = "https://api.twilio.com/2010-04-01"


class TwilioRestClient:
    """Thin wrapper around Twilio Voice Calls REST API."""

    def __init__(self, config: TwilioConfig, *, timeout: float = 20.0) -> None:
        self.config = config
        self.timeout = timeout

    def _auth(self) -> tuple[str, str]:
        return self.config.account_sid, self.config.auth_token

    async def create_call(
        self,
        *,
        to: str,
        from_number: str | None = None,
        url: str | None = None,
        twiml: str | None = None,
        status_callback: str | None = None,
        status_callback_event: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create an outbound call. Provide either ``url`` (TwiML webhook) or ``twiml``."""
        if not url and not twiml:
            raise ValueError("Either url or twiml is required to create a Twilio call")
        if url and twiml:
            raise ValueError("Provide only one of url or twiml")

        data: dict[str, Any] = {
            "To": to,
            "From": from_number or self.config.from_number,
        }
        if url:
            data["Url"] = url
            data["Method"] = "POST"
        if twiml:
            data["Twiml"] = twiml
        if status_callback:
            data["StatusCallback"] = status_callback
            data["StatusCallbackMethod"] = "POST"
            events = status_callback_event or ["initiated", "ringing", "answered", "completed"]
            # Twilio expects repeated StatusCallbackEvent fields
            data["StatusCallbackEvent"] = events

        endpoint = (
            f"{TWILIO_API_BASE}/Accounts/{self.config.account_sid}/Calls.json"
        )
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(endpoint, data=data, auth=self._auth())
        if response.status_code >= 400:
            logger.error(
                "twilio_create_call_failed status=%s body=%s",
                response.status_code,
                response.text[:500],
            )
            raise RuntimeError(
                f"Twilio create call failed ({response.status_code}): {response.text[:300]}"
            )
        return response.json()


def validate_twilio_signature(
    *,
    auth_token: str,
    signature: str,
    url: str,
    params: dict[str, str],
) -> bool:
    """Validate X-Twilio-Signature (HMAC-SHA1) for form-encoded webhooks."""
    if not auth_token or not signature:
        return False
    # Twilio: append sorted POST params as key+value (no delimiters) to the full URL
    pieces = [url]
    for key in sorted(params.keys()):
        pieces.append(key)
        pieces.append(params[key])
    payload = "".join(pieces).encode("utf-8")
    digest = hmac.new(auth_token.encode("utf-8"), payload, hashlib.sha1).digest()
    expected = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(expected, signature)


def build_query_url(base_url: str, query: dict[str, str]) -> str:
    cleaned = {k: v for k, v in query.items() if v}
    if not cleaned:
        return base_url
    return f"{base_url}?{urlencode(cleaned)}"
