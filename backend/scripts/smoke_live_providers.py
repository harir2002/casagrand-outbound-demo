"""Live provider smoke test (opt-in). Does not print secrets.

Run from backend/:
  .\\.venv\\Scripts\\python.exe scripts\\smoke_live_providers.py
"""

from __future__ import annotations

import asyncio
import sys
import wave
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import get_settings, reset_settings_cache  # noqa: E402
from app.models.call_view import TurnRequest  # noqa: E402
from app.models.session import CreateSessionRequest, Language  # noqa: E402
from app.providers.factory import build_provider_bundle, validate_live_provider_config  # noqa: E402
from app.services import call_service  # noqa: E402
from app.services.conversation_orchestrator import ConversationOrchestrator  # noqa: E402
from app.services.session_store import store  # noqa: E402


def _mask(value: str) -> str:
    if not value:
        return "(empty)"
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}…{value[-4:]} (len={len(value)})"


def _tiny_wav(duration_ms: int = 400, rate: int = 16000) -> bytes:
    """Generate a short silent WAV so Sarvam STT receives a valid file."""
    frames = int(rate * (duration_ms / 1000.0))
    buf = BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(b"\x00\x00" * frames)
    return buf.getvalue()


async def main() -> int:
    reset_settings_cache()
    settings = get_settings()
    print("=== Live provider smoke ===")
    print(f"APP_ENV={settings.app_env}")
    print(f"PROVIDER_MODE={settings.provider_mode}")
    print(f"STT={settings.stt_provider} TTS={settings.tts_provider} LLM={settings.llm_provider}")
    print(f"GROQ_MODEL={settings.groq_llm_model}")
    print(f"SARVAM_TTS_STREAMING={settings.sarvam_tts_streaming}")
    print(f"GROQ_STREAMING={settings.groq_streaming}")
    print(f"SARVAM_KEY={_mask(settings.sarvam_api_key)}")
    print(f"GROQ_KEY={_mask(settings.groq_api_key)}")

    problems = validate_live_provider_config(settings)
    if problems:
        print("CONFIG ERROR:")
        for p in problems:
            print(f"  - {p}")
        return 1

    try:
        bundle = build_provider_bundle(settings)
    except Exception as exc:  # noqa: BLE001
        print(f"BUNDLE ERROR: {type(exc).__name__}: {exc}")
        return 1

    print(f"Bundle OK: stt={bundle.stt_name} tts={bundle.tts_name} llm={bundle.llm_name} mode={bundle.mode}")
    failures: list[str] = []

    # 1) LLM
    try:
        llm = await bundle.llm.complete(
            "GROUNDED_ANSWER:\nCasagrand Highcity pricing starts at indicative demo rates.",
            Language.EN,
            system_prompt="Only rephrase. Do not invent facts.",
        )
        print(f"LLM OK provider={llm.provider} ms={llm.latency_ms} chars={len(llm.text)}")
    except Exception as exc:  # noqa: BLE001
        msg = f"LLM FAIL: {type(exc).__name__}: {exc}"
        print(msg)
        failures.append(msg)

    # 2) TTS
    try:
        tts = await bundle.tts.synthesize(
            "Hello from Casagrand Highcity demo.",
            Language.EN,
        )
        has_audio = bool(tts.audio_base64 or tts.audio_url)
        print(
            f"TTS OK provider={tts.provider} ms={tts.latency_ms} "
            f"audio={has_audio} mime={tts.mime_type} "
            f"transport={(tts.meta or {}).get('transport')} "
            f"streaming={(tts.meta or {}).get('streaming')} "
            f"fallback={(tts.meta or {}).get('fallback_used')} "
            f"first_audio={(tts.meta or {}).get('first_audio_ms')}"
        )
        if not has_audio:
            failures.append("TTS returned no audio payload")
    except Exception as exc:  # noqa: BLE001
        msg = f"TTS FAIL: {type(exc).__name__}: {exc}"
        print(msg)
        failures.append(msg)

    # 3) STT (silent wav — may return empty; failure means API/auth issue)
    try:
        stt = await bundle.stt.transcribe(_tiny_wav(), Language.EN, mime_type="audio/wav")
        print(
            f"STT OK provider={stt.provider} ms={stt.latency_ms} "
            f"text_len={len(stt.text)} conf={stt.confidence}"
        )
    except Exception as exc:  # noqa: BLE001
        msg = f"STT FAIL: {type(exc).__name__}: {exc}"
        print(msg)
        failures.append(msg)

    # 4) Orchestrator text turn (domain + parallel LLM∥TTS)
    store.clear()
    try:
        created = call_service.create_session(
            CreateSessionRequest(project_id="highcity", language=Language.EN)
        )
        orchestrator = ConversationOrchestrator(bundle)
        view = await orchestrator.handle_turn(
            TurnRequest(
                session_id=created.session.session_id,
                text="What is the pricing?",
                skip_llm=False,
            )
        )
        print(
            f"ORCH OK bucket={view.active_bucket} intent={view.last_intent} "
            f"llm={view.llm_provider} tts={view.tts_provider} "
            f"audio={bool(view.audio_base64 or view.audio_url)} "
            f"latency_ms={view.latency_ms}"
        )
        timings = (view.provider_meta or {}).get("timings") or {}
        print(
            "ORCH TIMINGS "
            f"stt={timings.get('stt_ms')} domain={timings.get('domain_ms')} "
            f"llm={timings.get('llm_ms')} tts={timings.get('tts_ms')} "
            f"stream_start={timings.get('stream_start_ms')} "
            f"first_audio={timings.get('first_audio_ms')} "
            f"parallel_wall={timings.get('parallel_wall_ms')} total={timings.get('total_ms')}"
        )
        print(
            "ORCH VOICE "
            f"tts_transport={(view.provider_meta or {}).get('tts_transport')} "
            f"tts_streaming={(view.provider_meta or {}).get('tts_streaming')} "
            f"tts_fallback={(view.provider_meta or {}).get('tts_fallback_used')} "
            f"llm_streaming={(view.provider_meta or {}).get('llm_streaming')}"
        )
        print(f"ORCH OPT={(view.provider_meta or {}).get('optimization')}")
        if view.warning:
            print(f"ORCH WARN: {view.warning}")
        if not view.reply_text:
            failures.append("Orchestrator returned empty reply_text")
        if timings.get("parallel_wall_ms") is None:
            failures.append("Missing parallel_wall_ms timing field")
        if timings.get("first_audio_ms") is None:
            failures.append("Missing first_audio_ms timing field")
        if timings.get("total_ms") is None:
            failures.append("Missing total_ms timing field")

        # 4b) End-to-end streaming cascade (Groq deltas → Sarvam WS → client events)
        stream_events = []
        async for ev in orchestrator.handle_turn_stream(
            TurnRequest(
                session_id=created.session.session_id,
                text="What amenities are available?",
                skip_llm=False,
            )
        ):
            stream_events.append(ev)
        names = [e.get("event") for e in stream_events]
        end = stream_events[-1] if stream_events else {}
        st = end.get("timings") or {}
        print(
            "STREAM ORCH "
            f"events={names} "
            f"first_audio={st.get('first_audio_ms')} total={st.get('total_ms')} "
            f"transport={end.get('transport')} fallback={end.get('fallback_used')} "
            f"audio_chunks={sum(1 for e in stream_events if e.get('event')=='audio_chunk')}"
        )
        if not stream_events or stream_events[0].get("event") != "stream_start":
            failures.append("Stream path missing stream_start")
        if "audio_chunk" not in names:
            failures.append("Stream path missing audio_chunk")
        if end.get("event") != "stream_end":
            failures.append("Stream path missing stream_end")
        if st.get("first_audio_ms") is None:
            failures.append("Stream path missing first_audio_ms")

        # Warm-path second aggregated turn (reused HTTP clients / WS path)
        view2 = await orchestrator.handle_turn(
            TurnRequest(
                session_id=created.session.session_id,
                text="Tell me about location",
                skip_llm=False,
            )
        )
        t2 = (view2.provider_meta or {}).get("timings") or {}
        print(
            "ORCH2 WARM "
            f"llm={t2.get('llm_ms')} tts={t2.get('tts_ms')} "
            f"first_audio={t2.get('first_audio_ms')} "
            f"parallel_wall={t2.get('parallel_wall_ms')} total={t2.get('total_ms')} "
            f"transport={(view2.provider_meta or {}).get('tts_transport')} "
            f"fallback={(view2.provider_meta or {}).get('tts_fallback_used')}"
        )

        # Explicit HTTP-only backup path still works (non-streaming smoke)
        from app.providers.tts.hybrid_sarvam_tts import HybridSarvamTTS
        from app.providers.tts.sarvam_tts import SarvamTTS

        http_tts = SarvamTTS(
            settings.sarvam_api_key,
            base_url=settings.sarvam_base_url,
            model=settings.sarvam_tts_model,
            speaker=settings.sarvam_tts_speaker,
            timeout_seconds=settings.provider_timeout_seconds,
            max_retries=settings.provider_max_retries,
        )
        backup = HybridSarvamTTS(http_tts, None, prefer_streaming=False)
        backup_result = await backup.synthesize(
            "Hello from Casagrand HTTP backup path.",
            Language.EN,
        )
        print(
            "TTS HTTP BACKUP OK "
            f"ms={backup_result.latency_ms} "
            f"transport={backup_result.meta.get('transport')} "
            f"audio={bool(backup_result.audio_base64)}"
        )
        if not backup_result.audio_base64:
            failures.append("HTTP backup TTS returned no audio")
    except Exception as exc:  # noqa: BLE001
        msg = f"ORCH FAIL: {type(exc).__name__}: {exc}"
        print(msg)
        failures.append(msg)
    finally:
        store.clear()

    if failures:
        print("=== SMOKE FAILED ===")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("=== SMOKE PASSED ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
