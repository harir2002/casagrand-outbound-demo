"""Telephony bridge behavior tests (stub orchestrator, no network)."""

from __future__ import annotations

import base64
import math
import struct

import pytest

from app.integrations.twilio.audio_codec import pcm16_to_mulaw, pcm16_to_wav_bytes
from app.integrations.twilio.media_streams import parse_stream_message
from app.models.call_view import CallViewResponse
from app.models.session import FlowBucket, Language
from app.services.session_store import store
from app.services.telephony_bridge import TelephonyBridge


def _loud_speech_mulaw(frames: int = 8, frame_samples: int = 160) -> list[bytes]:
    """Return several loud μ-law frames (above ambient VAD thresholds)."""
    out: list[bytes] = []
    for _ in range(frames):
        pcm = bytearray()
        for i in range(frame_samples):
            value = int(9000 * math.sin(2 * math.pi * 400 * i / 8000.0))
            pcm += struct.pack("<h", value)
        out.append(pcm16_to_mulaw(bytes(pcm)))
    return out


class _RecordingSender:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def send_json(self, data: dict) -> None:
        self.messages.append(data)


class _FakeOrchestrator:
    def __init__(self) -> None:
        self.calls = []
        self.speak_calls = []

    async def speak_text(self, text, language):
        from app.providers.types import SynthesisResult
        from app.services.audio_pipeline import SynthesizeOutcome

        self.speak_calls.append((text, language))
        pcm = b"\x00\x10" * 400
        wav = pcm16_to_wav_bytes(pcm, sample_rate=8000)
        audio_b64 = base64.b64encode(wav).decode("ascii")
        return SynthesizeOutcome(
            synthesis=SynthesisResult(
                text=text,
                audio_base64=audio_b64,
                mime_type="audio/wav",
                provider="stub",
                latency_ms=4.0,
            ),
            warning=None,
            latency_ms=4.0,
        )

    async def handle_turn(self, payload):
        self.calls.append(payload)
        pcm = b"\x00\x10" * 400
        wav = pcm16_to_wav_bytes(pcm, sample_rate=8000)
        audio_b64 = base64.b64encode(wav).decode("ascii")
        return CallViewResponse(
            session_id=payload.session_id,
            call_id=payload.session_id,
            active_project="highcity",
            active_language=payload.language or Language.EN,
            active_bucket=FlowBucket.INTRODUCTION,
            reply_text="Welcome to Casagrand Highcity.",
            audio_base64=audio_b64,
            audio_mime_type="audio/wav",
            provider_meta={
                "timings": {"total_ms": 12.5, "first_audio_ms": 4.0},
                "tts_fallback_used": False,
            },
            latency_ms=12.5,
        )


@pytest.mark.asyncio
async def test_bridge_connected_start_media_stop_flow(monkeypatch):
    store.clear()
    sender = _RecordingSender()
    orch = _FakeOrchestrator()
    bridge = TelephonyBridge(
        sender=sender,
        orchestrator=orch,  # type: ignore[arg-type]
        bidirectional=True,
        tts_sample_rate=8000,
    )
    # Lower thresholds for unit test
    bridge.MIN_SPEECH_BYTES = 80
    bridge.SILENCE_FRAMES_TO_COMMIT = 2
    bridge.MAX_UTTERANCE_BYTES = 10_000
    bridge.POST_TTS_ECHO_GUARD_SEC = 0.0
    bridge.SPEECH_START_FRAMES = 2

    await bridge.handle_message(
        parse_stream_message({"event": "connected", "protocol": "Call"})
    )
    await bridge.handle_message(
        parse_stream_message(
            {
                "event": "start",
                "start": {
                    "streamSid": "MZ1",
                    "callSid": "CA1",
                    "accountSid": "AC1",
                    "customParameters": {
                        "project_id": "highcity",
                        "language": "en",
                    },
                },
                "streamSid": "MZ1",
            }
        )
    )
    assert bridge.state is not None
    assert bridge.state.session_id
    # Intro is TTS-only (no fake user "hello" turn)
    assert orch.speak_calls
    assert not orch.calls
    # Bidirectional playback frames
    assert any(m.get("event") == "media" for m in sender.messages)

    # Simulate speech then silence → commit utterance
    silence = b"\xff" * 160
    silence_b64 = base64.b64encode(silence).decode("ascii")
    for frame in _loud_speech_mulaw(frames=6):
        await bridge.handle_message(
            parse_stream_message(
                {
                    "event": "media",
                    "streamSid": "MZ1",
                    "media": {
                        "track": "inbound",
                        "payload": base64.b64encode(frame).decode("ascii"),
                    },
                }
            )
        )
    for _ in range(3):
        await bridge.handle_message(
            parse_stream_message(
                {
                    "event": "media",
                    "streamSid": "MZ1",
                    "media": {"track": "inbound", "payload": silence_b64},
                }
            )
        )

    assert len(orch.calls) >= 1
    assert any(c.audio_base64 for c in orch.calls if hasattr(c, "audio_base64"))
    meta = bridge.metadata()
    assert meta["call_sid"] == "CA1"
    assert meta["stream_sid"] == "MZ1"
    assert meta["timings"]["turns"] >= 2

    await bridge.handle_message(
        parse_stream_message(
            {
                "event": "stop",
                "streamSid": "MZ1",
                "stop": {"callSid": "CA1", "accountSid": "AC1"},
            }
        )
    )
    assert bridge.state.closed is True
    store.clear()


@pytest.mark.asyncio
async def test_bridge_receive_only_skips_outbound_audio():
    store.clear()
    sender = _RecordingSender()
    orch = _FakeOrchestrator()
    bridge = TelephonyBridge(
        sender=sender,
        orchestrator=orch,  # type: ignore[arg-type]
        bidirectional=False,
    )
    await bridge.handle_message(
        parse_stream_message(
            {
                "event": "start",
                "start": {
                    "streamSid": "MZ2",
                    "callSid": "CA2",
                    "customParameters": {"project_id": "mercury", "language": "en"},
                },
                "streamSid": "MZ2",
            }
        )
    )
    # Intro TTS ran but no media frames sent back (receive-only)
    assert orch.speak_calls
    assert not orch.calls
    assert not any(m.get("event") == "media" for m in sender.messages)
    store.clear()


def test_twilio_status_endpoint(client, monkeypatch):
    monkeypatch.setenv("TWILIO_ENABLED", "false")
    from app.core.config import reset_settings_cache

    reset_settings_cache()
    response = client.get("/twilio/status")
    assert response.status_code == 200
    body = response.json()
    assert body["enabled"] is False
    assert body["ready"] is False
