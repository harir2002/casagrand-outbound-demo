"""Parse / emit Twilio Media Streams WebSocket messages."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StreamEventType(str, Enum):
    CONNECTED = "connected"
    START = "start"
    MEDIA = "media"
    DTMF = "dtmf"
    MARK = "mark"
    STOP = "stop"
    UNKNOWN = "unknown"


@dataclass
class StreamMessage:
    event: StreamEventType
    raw: dict[str, Any]
    sequence_number: str | None = None
    stream_sid: str | None = None
    call_sid: str | None = None
    account_sid: str | None = None
    custom_parameters: dict[str, str] = field(default_factory=dict)
    media_payload: bytes | None = None
    media_timestamp: str | None = None
    media_chunk: str | None = None
    media_track: str | None = None
    dtmf_digit: str | None = None
    mark_name: str | None = None


def parse_stream_message(data: str | bytes | dict[str, Any]) -> StreamMessage:
    """Parse a Twilio Media Streams JSON message into a typed structure."""
    if isinstance(data, (bytes, bytearray)):
        payload = json.loads(data.decode("utf-8"))
    elif isinstance(data, str):
        payload = json.loads(data)
    else:
        payload = data

    event_raw = str(payload.get("event") or "").lower()
    try:
        event = StreamEventType(event_raw)
    except ValueError:
        event = StreamEventType.UNKNOWN

    stream_sid = payload.get("streamSid") or payload.get("stream_sid")
    sequence = payload.get("sequenceNumber")
    call_sid = None
    account_sid = None
    custom: dict[str, str] = {}
    media_payload = None
    media_timestamp = None
    media_chunk = None
    media_track = None
    dtmf_digit = None
    mark_name = None

    if event == StreamEventType.START:
        start = payload.get("start") or {}
        stream_sid = stream_sid or start.get("streamSid")
        call_sid = start.get("callSid")
        account_sid = start.get("accountSid")
        custom = {
            str(k): str(v) for k, v in (start.get("customParameters") or {}).items()
        }
    elif event == StreamEventType.MEDIA:
        media = payload.get("media") or {}
        media_timestamp = media.get("timestamp")
        media_chunk = media.get("chunk")
        media_track = media.get("track")
        b64 = media.get("payload") or ""
        if b64:
            media_payload = base64.b64decode(b64)
    elif event == StreamEventType.DTMF:
        dtmf = payload.get("dtmf") or {}
        dtmf_digit = dtmf.get("digit")
    elif event == StreamEventType.MARK:
        mark = payload.get("mark") or {}
        mark_name = mark.get("name")
    elif event == StreamEventType.STOP:
        stop = payload.get("stop") or {}
        call_sid = stop.get("callSid") or call_sid
        account_sid = stop.get("accountSid") or account_sid
        stream_sid = stream_sid or stop.get("streamSid")

    return StreamMessage(
        event=event,
        raw=payload,
        sequence_number=str(sequence) if sequence is not None else None,
        stream_sid=stream_sid,
        call_sid=call_sid,
        account_sid=account_sid,
        custom_parameters=custom,
        media_payload=media_payload,
        media_timestamp=media_timestamp,
        media_chunk=media_chunk,
        media_track=media_track,
        dtmf_digit=dtmf_digit,
        mark_name=mark_name,
    )


def build_media_out_message(stream_sid: str, mulaw_payload: bytes) -> dict[str, Any]:
    """Outbound media frame Twilio expects for bidirectional streams."""
    return {
        "event": "media",
        "streamSid": stream_sid,
        "media": {
            "payload": base64.b64encode(mulaw_payload).decode("ascii"),
        },
    }


def build_clear_message(stream_sid: str) -> dict[str, Any]:
    return {"event": "clear", "streamSid": stream_sid}


def build_mark_message(stream_sid: str, name: str) -> dict[str, Any]:
    return {
        "event": "mark",
        "streamSid": stream_sid,
        "mark": {"name": name},
    }


def chunk_mulaw(mulaw: bytes, *, frame_bytes: int = 160) -> list[bytes]:
    """Split μ-law into ~20ms frames (160 bytes @ 8 kHz)."""
    if frame_bytes <= 0:
        return [mulaw] if mulaw else []
    return [mulaw[i : i + frame_bytes] for i in range(0, len(mulaw), frame_bytes) if mulaw[i : i + frame_bytes]]
