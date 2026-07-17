"""Minimal TwiML builders for Twilio Voice + Media Streams."""

from __future__ import annotations

import html
from typing import Mapping
from xml.sax.saxutils import escape


def build_media_stream_twiml(
    stream_wss_url: str,
    *,
    parameters: Mapping[str, str] | None = None,
    status_callback: str | None = None,
) -> str:
    """Return TwiML that connects the answered call to a bidirectional Media Stream."""
    url = escape(stream_wss_url.strip())
    params_xml = ""
    if parameters:
        chunks: list[str] = []
        for key, value in parameters.items():
            if value is None or value == "":
                continue
            chunks.append(
                f'      <Parameter name="{escape(str(key))}" value="{escape(str(value))}" />'
            )
        if chunks:
            params_xml = "\n" + "\n".join(chunks) + "\n    "
    status_attr = ""
    if status_callback:
        status_attr = f' statusCallback="{escape(status_callback.strip())}"'
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<Response>\n"
        "  <Connect>\n"
        f'    <Stream url="{url}"{status_attr}>{params_xml}</Stream>\n'
        "  </Connect>\n"
        "</Response>\n"
    )


def build_say_fallback_twiml(message: str) -> str:
    """Fallback TwiML when Media Streams cannot be configured."""
    safe = html.escape(message.strip() or "We are unable to connect the media stream.")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<Response>\n"
        f"  <Say>{safe}</Say>\n"
        "  <Hangup/>\n"
        "</Response>\n"
    )
