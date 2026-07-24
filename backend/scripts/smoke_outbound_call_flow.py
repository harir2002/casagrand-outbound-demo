"""Smoke test: full live outbound call application path.

Covers (without requiring a real phone answer by default):
  1. Phone number entry / E.164 validation
  2. Call initiation (Twilio REST — mocked unless SMOKE_LIVE_DIAL=1)
  3. Voice webhook → Media Stream TwiML
  4. TelephonyBridge → Sarvam STT + Sarvam TTS + Groq
  5. Transcript sync on shared session
  6. Session memory updates
  7. FAQ response (pricing)
  8. Human handoff summary

Run from backend/:
  .\\.venv\\Scripts\\python.exe scripts\\smoke_outbound_call_flow.py

Optional live dial (places a real Twilio call):
  $env:SMOKE_LIVE_DIAL='1'
  $env:SMOKE_TO_NUMBER='+91XXXXXXXXXX'
  .\\.venv\\Scripts\\python.exe scripts\\smoke_outbound_call_flow.py
"""

from __future__ import annotations

import asyncio
import base64
import os
import sys
import time
import wave
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import get_settings, reset_settings_cache  # noqa: E402
from app.integrations.twilio import call_registry  # noqa: E402
from app.integrations.twilio.audio_codec import pcm16_to_mulaw  # noqa: E402
from app.integrations.twilio.config import load_twilio_config, validate_twilio_config  # noqa: E402
from app.integrations.twilio.media_streams import parse_stream_message  # noqa: E402
from app.integrations.twilio.schemas import OutboundCallRequest, normalize_e164  # noqa: E402
from app.integrations.twilio.service import TwilioCallService  # noqa: E402
from app.kb.bootstrap import init_knowledge_base  # noqa: E402
from app.models.call_view import TurnRequest  # noqa: E402
from app.models.session import Language  # noqa: E402
from app.providers.factory import build_provider_bundle, validate_live_provider_config  # noqa: E402
from app.services import call_service  # noqa: E402
from app.services.conversation_orchestrator import ConversationOrchestrator  # noqa: E402
from app.services.session_memory import to_session_memory  # noqa: E402
from app.services.session_store import store  # noqa: E402
from app.services.telephony_bridge import TelephonyBridge  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from app.main import create_app  # noqa: E402


class _FakeTwilioClient:
    def __init__(self, config):
        self.config = config
        self.calls: list[dict] = []

    async def create_call(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "sid": "CA" + "smoke" + "0" * 28,
            "status": "queued",
            "direction": "outbound-api",
        }


class _RecordingSender:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def send_json(self, data: dict) -> None:
        self.messages.append(data)


def _mask(value: str) -> str:
    if not value:
        return "(empty)"
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}…{value[-4:]} (len={len(value)})"


def _tiny_wav(duration_ms: int = 500, rate: int = 16000) -> bytes:
    frames = int(rate * (duration_ms / 1000.0))
    buf = BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        # Soft non-silence so STT still accepts the payload.
        pcm = b"".join(
            (int(800 * ((i % 40) / 40.0 - 0.5)).to_bytes(2, "little", signed=True))
            for i in range(frames)
        )
        wf.writeframes(pcm)
    return buf.getvalue()


def _wav_ok(audio_base64: str | None) -> tuple[bool, str]:
    if not audio_base64:
        return False, "missing audio_base64"
    try:
        raw = base64.b64decode(audio_base64)
        with wave.open(BytesIO(raw), "rb") as wf:
            rate = wf.getframerate()
            frames = wf.getnframes()
            duration_ms = round(frames / max(rate, 1) * 1000, 1)
        if frames < 100:
            return False, "audio too short"
        return True, f"wav rate={rate} duration_ms={duration_ms}"
    except Exception as exc:  # noqa: BLE001
        return False, f"invalid wav: {exc}"


async def main() -> int:
    # TestClient webhook/status posts won't carry Twilio signatures.
    os.environ["TWILIO_VALIDATE_SIGNATURES"] = "false"
    reset_settings_cache()
    settings = get_settings()
    live_dial = os.getenv("SMOKE_LIVE_DIAL", "").strip() in {"1", "true", "yes"}
    to_number = (os.getenv("SMOKE_TO_NUMBER") or "+919876543210").strip()

    print("=== Outbound call flow smoke ===")
    print(f"STT={settings.stt_provider} TTS={settings.tts_provider} LLM={settings.llm_provider}")
    print(f"SARVAM_KEY={_mask(settings.sarvam_api_key)} GROQ_KEY={_mask(settings.groq_api_key)}")
    print(f"TWILIO_ENABLED={settings.twilio_enabled} live_dial={live_dial} to={to_number}")

    failures: list[str] = []
    timings: dict[str, float | None] = {}

    # --- 1) Phone number entry / validation ---
    print("\n--- 1) Number entry ---")
    bad = normalize_e164("12345")
    good = normalize_e164(to_number)
    print(f"invalid '12345' -> {bad!r}")
    print(f"customer number -> {good!r}")
    if good is None or not str(good).startswith("+"):
        failures.append("Phone number entry failed E.164 normalization")
    else:
        print("Number entry OK")

    # --- Providers + KB ---
    problems = validate_live_provider_config(settings)
    if problems:
        print("PROVIDER CONFIG ERROR:")
        for p in problems:
            print(f"  - {p}")
        return 1

    kb = init_knowledge_base(settings)
    print(f"KB source={kb.get('source')} docs={kb.get('document_count')}")

    bundle = build_provider_bundle(settings)
    if bundle.stt_name != "sarvam" or bundle.tts_name != "sarvam":
        failures.append(f"Expected Sarvam STT+TTS, got stt={bundle.stt_name} tts={bundle.tts_name}")
    orchestrator = ConversationOrchestrator(bundle)

    # --- 2) Call initiation ---
    print("\n--- 2) Call initiation ---")
    store.clear()
    call_registry.clear()
    cfg = load_twilio_config(settings)
    twilio_problems = validate_twilio_config(cfg)
    print(f"Twilio ready={cfg.enabled and not twilio_problems} problems={twilio_problems or 'none'}")

    if not cfg.enabled:
        failures.append("TWILIO_ENABLED must be true for outbound smoke")
        print("\n=== SMOKE FAILED (telephony disabled) ===")
        for f in failures:
            print(f"  - {f}")
        return 1

    # For mocked dial we still need credentials present so config loads.
    if twilio_problems and not live_dial:
        print(
            "NOTE: Twilio config incomplete for live dial; "
            "continuing with mocked REST client for initiation path."
        )

    customer_name = "Anitha Raman"
    init_started = time.perf_counter()
    if live_dial:
        if twilio_problems:
            failures.append(f"Cannot live-dial: {twilio_problems}")
            print("\n=== SMOKE FAILED ===")
            for f in failures:
                print(f"  - {f}")
            return 1
        service = TwilioCallService(config=cfg)
        call = await service.start_outbound_call(
            OutboundCallRequest(
                to=good,
                customer_name=customer_name,
                project_id="highcity",
                language=Language.EN,
            )
        )
        print(f"LIVE DIAL placed call_sid={call.call_sid} status={call.status}")
    else:
        # Ensure config object exists even if public URL is stale — use loaded cfg
        # but swap REST client for a fake.
        if twilio_problems:
            # Build a minimal ready-looking config for the service layer by
            # temporarily requiring only what the fake client needs.
            from app.integrations.twilio.config import TwilioConfig

            cfg = TwilioConfig(
                enabled=True,
                account_sid=settings.twilio_account_sid or "ACsmoke",
                auth_token=settings.twilio_auth_token or "token",
                from_number=settings.twilio_from_number or "+15551234567",
                public_base_url=settings.twilio_public_base_url
                or "https://demo.example.ngrok.app",
                media_stream_path=settings.twilio_media_stream_path,
                voice_webhook_path=settings.twilio_voice_webhook_path,
                status_callback_path=settings.twilio_status_callback_path,
                validate_signatures=False,
            )
        fake = _FakeTwilioClient(cfg)
        service = TwilioCallService(config=cfg, client=fake)
        call = await service.start_outbound_call(
            OutboundCallRequest(
                to=good,
                customer_name=customer_name,
                project_id="highcity",
                language=Language.EN,
            )
        )
        assert fake.calls, "Twilio create_call was not invoked"
        print(f"INITIATE OK (mocked REST) call_sid={call.call_sid} to={call.to}")

    timings["initiate_ms"] = round((time.perf_counter() - init_started) * 1000, 2)
    session_id = call.session_id
    if not session_id:
        failures.append("Outbound call missing session_id")
        print("\n=== SMOKE FAILED ===")
        for f in failures:
            print(f"  - {f}")
        return 1
    if call.to != good:
        failures.append(f"Call to mismatch: {call.to} != {good}")
    if (call.provider_meta or {}).get("customer_name") != customer_name:
        # provider_meta may omit name; check session memory instead
        sess = call_service.get_session(session_id).session
        if sess.memory.caller_name != customer_name:
            failures.append("Customer name not stored on session memory")
    print(f"session_id={session_id} initiate_ms={timings['initiate_ms']}")

    # --- 3) Voice webhook TwiML ---
    print("\n--- 3) Voice webhook / Media Stream TwiML ---")
    app = create_app()
    client = TestClient(app)
    webhook = client.post(
        "/twilio/voice-webhook",
        params={
            "session_id": session_id,
            "project_id": "highcity",
            "language": "en",
        },
    )
    if webhook.status_code != 200 or "<Connect>" not in webhook.text:
        failures.append(f"Voice webhook failed status={webhook.status_code}")
        print(f"WEBHOOK FAIL status={webhook.status_code}")
    else:
        print("WEBHOOK OK Connect/Stream TwiML")
        if session_id not in webhook.text:
            failures.append("TwiML missing session_id parameter")

    # --- 4) Bridge: STT + TTS live path ---
    print("\n--- 4) TelephonyBridge STT/TTS (Sarvam) ---")
    sender = _RecordingSender()
    bridge = TelephonyBridge(
        sender=sender, orchestrator=orchestrator, bidirectional=True
    )
    bridge.MIN_SPEECH_BYTES = 80
    bridge.SILENCE_FRAMES_TO_COMMIT = 2

    await bridge.handle_raw_message('{"event": "connected", "protocol": "Call"}')
    await bridge.handle_message(
        parse_stream_message(
            {
                "event": "start",
                "start": {
                    "streamSid": "MZsmoke",
                    "callSid": call.call_sid,
                    "customParameters": {
                        "session_id": session_id,
                        "project_id": "highcity",
                        "language": "en",
                    },
                },
                "streamSid": "MZsmoke",
            }
        )
    )

    # Intro turn should produce outbound media (TTS)
    media_out = [m for m in sender.messages if m.get("event") == "media"]
    print(f"intro media_out frames={len(media_out)} reply={bridge.state.last_reply_text!r}")
    if not media_out:
        failures.append("Bridge intro produced no TTS media-out frames")
    if not bridge.state.last_reply_text:
        failures.append("Bridge intro missing agent reply text")

    # Caller utterance via μ-law → STT → TTS
    stt_started = time.perf_counter()
    speech_b64 = base64.b64encode(pcm16_to_mulaw(b"\x80\x00" * 400)).decode("ascii")
    silence_b64 = base64.b64encode(b"\xff" * 160).decode("ascii")
    await bridge.handle_message(
        parse_stream_message(
            {
                "event": "media",
                "streamSid": "MZsmoke",
                "media": {"track": "inbound", "payload": speech_b64},
            }
        )
    )
    for _ in range(3):
        await bridge.handle_message(
            parse_stream_message(
                {
                    "event": "media",
                    "streamSid": "MZsmoke",
                    "media": {"track": "inbound", "payload": silence_b64},
                }
            )
        )
    timings["bridge_utterance_ms"] = round((time.perf_counter() - stt_started) * 1000, 2)
    meta = bridge.metadata()
    print(
        f"BRIDGE OK turns={meta['timings']['turns']} "
        f"last_reply={meta.get('last_reply_text')!r} "
        f"utterance_ms={timings['bridge_utterance_ms']}"
    )
    if meta["timings"]["turns"] < 1:
        failures.append("Bridge recorded no turns")

    # Direct STT check (explicit)
    try:
        stt = await bundle.stt.transcribe(_tiny_wav(), Language.EN, mime_type="audio/wav")
        timings["stt_ms"] = stt.latency_ms
        print(f"STT OK provider={stt.provider} ms={stt.latency_ms}")
        if stt.provider != "sarvam":
            failures.append(f"STT provider={stt.provider}")
    except Exception as exc:  # noqa: BLE001
        failures.append(f"STT FAIL: {exc}")

    # --- 5) Transcript sync ---
    print("\n--- 5) Transcript sync ---")
    session_after = call_service.get_session(session_id).session
    turns = session_after.transcript or []
    print(f"transcript turns={len(turns)}")
    for t in turns[-4:]:
        role = getattr(t, "role", None) or (t.get("role") if isinstance(t, dict) else "?")
        text = getattr(t, "text", None) or (t.get("text") if isinstance(t, dict) else "")
        print(f"  [{role}] {str(text)[:80]}")
    if len(turns) < 2:
        failures.append("Transcript sync: expected agent+user turns on session")
    else:
        print("Transcript sync OK")

    # Poll endpoint used by UI
    state_resp = client.get("/session/state", params={"session_id": session_id})
    if state_resp.status_code != 200:
        failures.append(f"/session/state failed: {state_resp.status_code}")
    else:
        body = state_resp.json()
        ui_turns = body.get("transcript") or []
        print(f"UI /session/state transcript turns={len(ui_turns)}")
        if len(ui_turns) < 1:
            failures.append("UI session state missing transcript")

    # --- 6) Memory ---
    print("\n--- 6) Context memory ---")
    memory = to_session_memory(session_after)
    print(
        f"MEMORY project={memory.active_project} lang={memory.active_language.value} "
        f"customer={session_after.memory.caller_name!r} "
        f"last_q={memory.last_question!r} handoff={memory.needs_handoff}"
    )
    if session_after.memory.caller_name != customer_name:
        failures.append("Memory missing customer_name from outbound initiate")
    if memory.active_project != "highcity":
        failures.append("Memory active_project mismatch")

    # --- 7) FAQ response ---
    print("\n--- 7) FAQ response ---")
    faq_started = time.perf_counter()
    faq_view = await orchestrator.handle_turn(
        TurnRequest(
            session_id=session_id,
            text="What is the pricing for Highcity?",
            skip_llm=False,
        )
    )
    timings["faq_total_ms"] = round((time.perf_counter() - faq_started) * 1000, 2)
    timings["faq_tts_ms"] = (faq_view.provider_meta or {}).get("timings", {}).get("tts_ms")
    timings["faq_llm_ms"] = (faq_view.provider_meta or {}).get("timings", {}).get("llm_ms")
    timings["faq_rag_ms"] = (faq_view.provider_meta or {}).get("timings", {}).get("rag_ms")
    ok, detail = _wav_ok(faq_view.audio_base64)
    print(
        f"FAQ OK intent={faq_view.last_intent} tts={faq_view.tts_provider} "
        f"audio={ok} {detail} total_ms={timings['faq_total_ms']}"
    )
    print(f"FAQ reply: {(faq_view.reply_text or '')[:120]}")
    if not faq_view.reply_text:
        failures.append("FAQ returned empty reply")
    if not ok:
        failures.append(f"FAQ TTS not playable: {detail}")
    if faq_view.tts_provider != "sarvam":
        failures.append(f"FAQ tts_provider={faq_view.tts_provider}")

    mem2 = to_session_memory(call_service.get_session(session_id).session)
    if not mem2.last_question:
        failures.append("Memory last_question not updated after FAQ")
    else:
        print(f"Memory after FAQ last_q={mem2.last_question!r} sources={mem2.last_rag_sources}")

    # --- 8) Human handoff ---
    print("\n--- 8) Human handoff ---")
    handoff_view = await orchestrator.handle_turn(
        TurnRequest(
            session_id=session_id,
            text="Please connect me to a human agent",
            skip_llm=False,
        )
    )
    sess_h = call_service.get_session(session_id).session
    mem_h = to_session_memory(sess_h)
    handoff_reason = (
        mem_h.handoff_reason
        or getattr(handoff_view, "handoff_reason", None)
        or sess_h.memory.handoff_reason
    )
    summary_text = (
        mem_h.summary
        or sess_h.final_summary
        or getattr(handoff_view, "summary", None)
        or ""
    )
    print(
        f"HANDOFF needs={sess_h.needs_handoff or handoff_view.needs_handoff or mem_h.needs_handoff} "
        f"reason={handoff_reason!r} "
        f"summary={str(summary_text)[:100]!r}"
    )
    if not (sess_h.needs_handoff or handoff_view.needs_handoff or mem_h.needs_handoff):
        intent = str(handoff_view.last_intent or "")
        if "handoff" not in intent.lower() and not summary_text:
            failures.append("Handoff path did not set needs_handoff or summary")
        else:
            print(f"HANDOFF OK via intent={intent}")
    else:
        print("HANDOFF OK")

    # Status callback completion (UI poll path)
    for status in ("ringing", "in-progress", "completed"):
        client.post(
            "/twilio/status-callback",
            data={"CallSid": call.call_sid, "CallStatus": status, "CallDuration": "42"},
        )
    status_view = client.get(
        "/twilio/call-status", params={"call_sid": call.call_sid}
    ).json()
    print(f"CALL STATUS terminal={status_view.get('terminal')} status={status_view.get('status')}")
    if not status_view.get("terminal"):
        failures.append("Call status did not reach terminal completed")

    await bridge.handle_message(
        parse_stream_message(
            {"event": "stop", "streamSid": "MZsmoke", "stop": {"callSid": call.call_sid}}
        )
    )

    # Latency table
    print("\n=== Latency breakdown (ms) ===")
    for key in (
        "initiate_ms",
        "stt_ms",
        "bridge_utterance_ms",
        "faq_rag_ms",
        "faq_llm_ms",
        "faq_tts_ms",
        "faq_total_ms",
    ):
        print(f"  {key:22} {timings.get(key) if timings.get(key) is not None else '—'}")

    store.clear()
    call_registry.clear()

    if failures:
        print("\n=== SMOKE FAILED ===")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("\n=== SMOKE PASSED ===")
    print(
        "Outbound ready: number entry -> Initiate -> Twilio webhook/stream -> "
        "Sarvam STT/TTS -> transcript/memory/FAQ/handoff."
    )
    if not live_dial:
        print(
            "Note: REST dial was mocked. For a real ring, set SMOKE_LIVE_DIAL=1 "
            "and SMOKE_TO_NUMBER=+E164 with a reachable ngrok URL."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
