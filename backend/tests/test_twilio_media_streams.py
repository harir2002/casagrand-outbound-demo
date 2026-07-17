"""Media Streams message parsing / outbound frame tests."""

from __future__ import annotations

import base64
import json

from app.integrations.twilio.audio_codec import mulaw_to_pcm16, pcm16_to_mulaw
from app.integrations.twilio.media_streams import (
    StreamEventType,
    build_clear_message,
    build_media_out_message,
    chunk_mulaw,
    parse_stream_message,
)


def test_parse_connected_event():
    msg = parse_stream_message(
        {"event": "connected", "protocol": "Call", "version": "1.0.0"}
    )
    assert msg.event == StreamEventType.CONNECTED


def test_parse_start_event_custom_parameters():
    raw = {
        "event": "start",
        "sequenceNumber": "1",
        "start": {
            "streamSid": "MZxxx",
            "callSid": "CAxxx",
            "accountSid": "ACxxx",
            "tracks": ["inbound"],
            "customParameters": {
                "session_id": "sess-42",
                "project_id": "highcity",
                "language": "en",
            },
        },
        "streamSid": "MZxxx",
    }
    msg = parse_stream_message(json.dumps(raw))
    assert msg.event == StreamEventType.START
    assert msg.stream_sid == "MZxxx"
    assert msg.call_sid == "CAxxx"
    assert msg.custom_parameters["session_id"] == "sess-42"


def test_parse_media_event_payload():
    mulaw = pcm16_to_mulaw(b"\x00\x01" * 80)
    payload = base64.b64encode(mulaw).decode("ascii")
    msg = parse_stream_message(
        {
            "event": "media",
            "streamSid": "MZxxx",
            "media": {
                "track": "inbound",
                "chunk": "1",
                "timestamp": "5",
                "payload": payload,
            },
        }
    )
    assert msg.event == StreamEventType.MEDIA
    assert msg.media_payload == mulaw
    assert mulaw_to_pcm16(msg.media_payload)


def test_parse_dtmf_and_stop():
    dtmf = parse_stream_message(
        {"event": "dtmf", "streamSid": "MZxxx", "dtmf": {"digit": "1"}}
    )
    assert dtmf.event == StreamEventType.DTMF
    assert dtmf.dtmf_digit == "1"

    stop = parse_stream_message(
        {
            "event": "stop",
            "streamSid": "MZxxx",
            "stop": {"callSid": "CAxxx", "accountSid": "ACxxx"},
        }
    )
    assert stop.event == StreamEventType.STOP
    assert stop.call_sid == "CAxxx"


def test_outbound_media_and_clear_messages():
    frame = b"\xff" * 160
    media = build_media_out_message("MZxxx", frame)
    assert media["event"] == "media"
    assert media["streamSid"] == "MZxxx"
    assert base64.b64decode(media["media"]["payload"]) == frame

    clear = build_clear_message("MZxxx")
    assert clear == {"event": "clear", "streamSid": "MZxxx"}

    chunks = chunk_mulaw(b"\xff" * 400, frame_bytes=160)
    assert len(chunks) == 3
    assert sum(len(c) for c in chunks) == 400
