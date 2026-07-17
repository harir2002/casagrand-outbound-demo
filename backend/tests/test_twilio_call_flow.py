"""End-to-end telephony flow tests (stub providers + mocked Twilio REST).

Covers: outbound call → voice webhook TwiML → media stream bridge (STT/LLM/TTS
via stub pipeline) → status callbacks → call completion. No live network.
"""

from __future__ import annotations

import base64
import re

import pytest

from app.core.config import reset_settings_cache
from app.integrations.twilio import call_registry
from app.integrations.twilio.audio_codec import pcm16_to_mulaw
from app.integrations.twilio.config import load_twilio_config
from app.integrations.twilio.media_streams import parse_stream_message
from app.integrations.twilio.schemas import OutboundCallRequest
from app.integrations.twilio.service import TwilioCallService
from app.models.session import FlowBucket
from app.providers.factory import ProviderBundle
from app.services import call_service
from app.services.conversation_orchestrator import ConversationOrchestrator
from app.services.session_store import store
from app.services.telephony_bridge import TelephonyBridge
from tests.doubles.providers import StubLLM, StubSTT, StubTTS


class _FakeTwilioClient:
    def __init__(self, config):
        self.config = config
        self.calls = []

    async def create_call(self, **kwargs):
        self.calls.append(kwargs)
        return {"sid": "CAflow", "status": "queued", "direction": "outbound-api"}


class _RecordingSender:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def send_json(self, data: dict) -> None:
        self.messages.append(data)


def _twilio_env(monkeypatch):
    monkeypatch.setenv("TWILIO_ENABLED", "true")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACxxxxxxxx")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO_FROM_NUMBER", "+15551234567")
    monkeypatch.setenv("TWILIO_PUBLIC_BASE_URL", "https://demo.example.ngrok.app")
    monkeypatch.setenv("TWILIO_VALIDATE_SIGNATURES", "false")
    reset_settings_cache()


def _stub_orchestrator() -> ConversationOrchestrator:
    bundle = ProviderBundle(
        stt=StubSTT(),
        tts=StubTTS(),
        llm=StubLLM(),
        stt_name="stub",
        tts_name="stub",
        llm_name="stub",
        mode="test",
    )
    return ConversationOrchestrator(bundle)


@pytest.mark.asyncio
async def test_full_call_flow_outbound_to_bridge(client, monkeypatch):
    """Outbound call → webhook TwiML → media stream bridge → pipeline turn → completion."""
    _twilio_env(monkeypatch)
    store.clear()
    call_registry.clear()

    # 1) Outbound call initiation (mocked Twilio REST)
    cfg = load_twilio_config()
    fake_client = _FakeTwilioClient(cfg)
    service = TwilioCallService(config=cfg, client=fake_client)
    call = await service.start_outbound_call(
        OutboundCallRequest(to="+91 98888-77777", project_id="highcity", language="en")
    )
    assert call.call_sid == "CAflow"
    assert call.to == "+919888877777"  # normalized E.164
    session_id = call.session_id
    assert call.twiml_url and "session_id=" in call.twiml_url

    # 2) Twilio answers → voice webhook returns Connect/Stream TwiML with session params
    webhook = client.post(
        "/twilio/voice-webhook",
        params={"session_id": session_id, "project_id": "highcity", "language": "en"},
    )
    assert webhook.status_code == 200
    twiml = webhook.text
    assert "<Connect>" in twiml
    match = re.search(r'value="([0-9a-f-]{36})"', twiml)
    assert match, "TwiML must carry the session_id parameter"
    assert session_id in twiml

    # 3) Media stream connects and bridges audio through the pipeline
    sender = _RecordingSender()
    bridge = TelephonyBridge(
        sender=sender, orchestrator=_stub_orchestrator(), bidirectional=True
    )
    bridge.MIN_SPEECH_BYTES = 80
    bridge.SILENCE_FRAMES_TO_COMMIT = 2

    await bridge.handle_raw_message('{"event": "connected", "protocol": "Call"}')
    await bridge.handle_message(
        parse_stream_message(
            {
                "event": "start",
                "start": {
                    "streamSid": "MZflow",
                    "callSid": call.call_sid,
                    "customParameters": {
                        "session_id": session_id,
                        "project_id": "highcity",
                        "language": "en",
                    },
                },
                "streamSid": "MZflow",
            }
        )
    )
    assert bridge.state.session_id == session_id  # session preserved across layers

    # Caller speech then silence → utterance committed → STT→LLM→TTS turn
    speech_b64 = base64.b64encode(pcm16_to_mulaw(b"\x80\x00" * 200)).decode("ascii")
    silence_b64 = base64.b64encode(b"\xff" * 160).decode("ascii")
    await bridge.handle_message(
        parse_stream_message(
            {
                "event": "media",
                "streamSid": "MZflow",
                "media": {"track": "inbound", "payload": speech_b64},
            }
        )
    )
    for _ in range(3):
        await bridge.handle_message(
            parse_stream_message(
                {
                    "event": "media",
                    "streamSid": "MZflow",
                    "media": {"track": "inbound", "payload": silence_b64},
                }
            )
        )

    meta = bridge.metadata()
    assert meta["timings"]["turns"] >= 2  # intro + caller utterance
    assert meta["last_reply_text"]

    # Session state advanced in the shared store (same four-bucket flow)
    session_after = call_service.get_session(session_id).session
    assert len(session_after.transcript) >= 2
    assert session_after.flow_bucket in list(FlowBucket)

    # 4) Stop event closes the bridge cleanly
    await bridge.handle_message(
        parse_stream_message(
            {"event": "stop", "streamSid": "MZflow", "stop": {"callSid": call.call_sid}}
        )
    )
    assert bridge.state.closed is True

    # 5) Status callbacks drive the registry to completion
    for status in ("ringing", "answered", "completed"):
        response = client.post(
            "/twilio/status-callback",
            data={"CallSid": call.call_sid, "CallStatus": status, "CallDuration": "31"},
        )
        assert response.status_code == 200

    status_view = client.get(
        "/twilio/call-status", params={"call_sid": call.call_sid}
    ).json()
    assert status_view["status"] == "completed"
    assert status_view["terminal"] is True
    assert status_view["session_id"] == session_id
    assert "ringing" in status_view["history"]

    store.clear()
    call_registry.clear()


def test_session_endpoints_unchanged_after_twilio(client, monkeypatch):
    """Local demo path still works with telephony enabled."""
    _twilio_env(monkeypatch)
    start = client.post(
        "/session/start", json={"project_id": "highcity", "language": "en"}
    )
    assert start.status_code == 200
    session_id = start.json()["session_id"]

    turn = client.post(
        "/session/turn",
        json={"session_id": session_id, "text": "What is the pricing?"},
    )
    assert turn.status_code == 200
    assert turn.json().get("reply_text")

    import json as _json

    with client.stream(
        "POST",
        "/session/turn/stream",
        json={"session_id": session_id, "text": "Tell me about amenities"},
    ) as response:
        assert response.status_code == 200
        lines = [ln for ln in response.iter_lines() if ln]
    events = [_json.loads(ln) for ln in lines]
    assert events[0]["event"] == "stream_start"
    assert events[-1]["event"] == "stream_end"
    assert any(e["event"] == "audio_chunk" for e in events)
