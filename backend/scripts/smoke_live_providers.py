"""Live provider smoke + latency validation for Sarvam STT + TTS outbound voice flow.

Run from backend/:
  .\\.venv\\Scripts\\python.exe scripts\\smoke_live_providers.py

Does not print secrets. Exercises:
  STT (Sarvam) → LLM (Groq) → TTS (Sarvam) → stream path → Twilio mulaw.
"""

from __future__ import annotations

import asyncio
import base64
import sys
import time
import wave
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import get_settings, reset_settings_cache  # noqa: E402
from app.integrations.twilio.audio_codec import pcm_or_wav_to_mulaw  # noqa: E402
from app.kb.bootstrap import init_knowledge_base  # noqa: E402
from app.models.call_view import TurnRequest  # noqa: E402
from app.models.session import CreateSessionRequest, Language  # noqa: E402
from app.providers.factory import build_provider_bundle, validate_live_provider_config  # noqa: E402
from app.services import call_service  # noqa: E402
from app.services.conversation_orchestrator import ConversationOrchestrator  # noqa: E402
from app.services.session_memory import to_session_memory  # noqa: E402
from app.services.session_store import store  # noqa: E402

BASELINE = {
    "first_audio_ms": 900.0,
    "total_turn_ms": 1300.0,
    "tts_ms": 1000.0,
}

SLOW_FLAGS = {
    "provider_init_ms": 2000.0,
    "llm_ms": 2500.0,
    "tts_ms": 3500.0,
    "first_audio_ms": 2500.0,
    "total_turn_ms": 5000.0,
}


def _mask(value: str) -> str:
    if not value:
        return "(empty)"
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}…{value[-4:]} (len={len(value)})"


def _tiny_wav(duration_ms: int = 400, rate: int = 16000) -> bytes:
    frames = int(rate * (duration_ms / 1000.0))
    buf = BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(b"\x00\x00" * frames)
    return buf.getvalue()


def _wav_ok(audio_base64: str | None) -> tuple[bool, str]:
    if not audio_base64:
        return False, "missing audio_base64"
    try:
        raw = base64.b64decode(audio_base64)
        with wave.open(BytesIO(raw), "rb") as wf:
            rate = wf.getframerate()
            channels = wf.getnchannels()
            frames = wf.getnframes()
            duration_ms = round(frames / max(rate, 1) * 1000, 1)
        if channels != 1:
            return False, f"expected mono, got channels={channels}"
        if frames < 100:
            return False, "audio too short"
        return True, f"wav rate={rate} duration_ms={duration_ms}"
    except Exception as exc:  # noqa: BLE001
        return False, f"invalid wav: {exc}"


def _flag(name: str, value: float | None) -> str:
    if value is None:
        return "missing"
    limit = SLOW_FLAGS.get(name)
    if limit is not None and value > limit:
        return f"SLOW (>{limit:.0f}ms)"
    return "ok"


def _compare(name: str, value: float | None) -> str:
    base = BASELINE.get(name)
    if value is None or base is None:
        return "-"
    delta = value - base
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.0f}ms vs Sarvam baseline {base:.0f}ms"


async def main() -> int:
    reset_settings_cache()
    settings = get_settings()
    print("=== Live provider smoke + latency ===")
    print("--- Active provider configuration ---")
    print(f"APP_ENV={settings.app_env} PROVIDER_MODE={settings.provider_mode}")
    print(f"STT={settings.stt_provider} model={settings.sarvam_stt_model}")
    print(
        f"TTS={settings.tts_provider} speaker={settings.sarvam_tts_speaker} "
        f"model={settings.sarvam_tts_model} streaming={settings.sarvam_tts_streaming}"
    )
    print(f"LLM={settings.llm_provider} model={settings.groq_llm_model} stream={settings.groq_streaming}")
    print(f"SARVAM_KEY={_mask(settings.sarvam_api_key)}")
    print(f"GROQ_KEY={_mask(settings.groq_api_key)}")

    kb_status = init_knowledge_base(settings)
    print(
        f"KB source={kb_status.get('source')} rag_backend={kb_status.get('backend')} "
        f"docs={kb_status.get('document_count')} build_ms={kb_status.get('build_ms')}"
    )

    problems = validate_live_provider_config(settings)
    if problems:
        print("CONFIG ERROR:")
        for p in problems:
            print(f"  - {p}")
        return 1

    failures: list[str] = []
    init_started = time.perf_counter()
    try:
        bundle = build_provider_bundle(settings)
    except Exception as exc:  # noqa: BLE001
        print(f"BUNDLE ERROR: {type(exc).__name__}: {exc}")
        return 1
    provider_init_ms = round((time.perf_counter() - init_started) * 1000, 2)
    print(
        f"Bundle OK: stt={bundle.stt_name} tts={bundle.tts_name} "
        f"llm={bundle.llm_name} mode={bundle.mode} init_ms={provider_init_ms}"
    )
    if bundle.stt_name != "sarvam":
        failures.append(f"Expected sarvam STT, got {bundle.stt_name}")
    if bundle.tts_name != "sarvam":
        failures.append(f"Expected sarvam TTS, got {bundle.tts_name}")

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
        llm = None

    # 2) TTS English + Tamil sample
    tts_en = None
    try:
        tts_en = await bundle.tts.synthesize(
            "Hello from Casagrand Highcity demo.",
            Language.EN,
        )
        ok, detail = _wav_ok(tts_en.audio_base64)
        print(
            f"TTS EN OK provider={tts_en.provider} "
            f"speaker={(tts_en.meta or {}).get('speaker')} "
            f"model={(tts_en.meta or {}).get('model')} ms={tts_en.latency_ms} "
            f"first_audio={(tts_en.meta or {}).get('first_audio_ms')} "
            f"transport={(tts_en.meta or {}).get('transport')} "
            f"fallback={(tts_en.meta or {}).get('fallback_used')} {detail}"
        )
        if not ok:
            failures.append(f"TTS EN audio not playable: {detail}")
        if tts_en.provider != "sarvam":
            failures.append(f"TTS EN provider={tts_en.provider}, expected sarvam")
    except Exception as exc:  # noqa: BLE001
        msg = f"TTS EN FAIL: {type(exc).__name__}: {exc}"
        print(msg)
        failures.append(msg)

    try:
        tts_ta = await bundle.tts.synthesize(
            "வணக்கம், காசகிராண்ட் ஹைசிட்டி பற்றி தெரிந்துகொள்ளலாம்.",
            Language.TA,
        )
        ok, detail = _wav_ok(tts_ta.audio_base64)
        print(
            f"TTS TA OK provider={tts_ta.provider} ms={tts_ta.latency_ms} "
            f"first_audio={(tts_ta.meta or {}).get('first_audio_ms')} {detail}"
        )
        if not ok:
            failures.append(f"TTS TA audio not playable: {detail}")
    except Exception as exc:  # noqa: BLE001
        msg = f"TTS TA FAIL: {type(exc).__name__}: {exc}"
        print(msg)
        failures.append(msg)

    # 3) STT
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

    # 4) Orchestrator aggregated + streaming + Twilio mulaw
    store.clear()
    stream_first_audio = None
    stream_total = None
    agg_timings: dict = {}
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
        agg_timings = (view.provider_meta or {}).get("timings") or {}
        ok, detail = _wav_ok(view.audio_base64)
        print(
            f"ORCH OK bucket={view.active_bucket} intent={view.last_intent} "
            f"llm={view.llm_provider} tts={view.tts_provider} "
            f"audio={ok} {detail} latency_ms={view.latency_ms}"
        )
        print(
            "ORCH TIMINGS "
            f"stt={agg_timings.get('stt_ms')} domain={agg_timings.get('domain_ms')} "
            f"rag={agg_timings.get('rag_ms')} "
            f"llm={agg_timings.get('llm_ms')} tts={agg_timings.get('tts_ms')} "
            f"stream_start={agg_timings.get('stream_start_ms')} "
            f"first_audio={agg_timings.get('first_audio_ms')} "
            f"parallel_wall={agg_timings.get('parallel_wall_ms')} "
            f"total={agg_timings.get('total_ms')}"
        )
        memory = None
        try:
            live = call_service.get_session(created.session.session_id).session
            memory = to_session_memory(live)
        except Exception:  # noqa: BLE001
            memory = None
        if memory is not None:
            print(
                "MEMORY "
                f"project={memory.active_project} lang={memory.active_language.value} "
                f"last_q={memory.last_question!r} handoff={memory.needs_handoff} "
                f"sources={memory.last_rag_sources}"
            )
            if not memory.last_question:
                failures.append("Session memory last_question not updated")
        if bundle.stt_name != "sarvam":
            failures.append(f"STT expected sarvam, got {bundle.stt_name}")
        if bundle.tts_name != "sarvam":
            failures.append(f"TTS expected sarvam, got {bundle.tts_name}")
        if bundle.llm_name != "groq":
            failures.append(f"LLM expected groq, got {bundle.llm_name}")
        if not view.reply_text:
            failures.append("Orchestrator returned empty reply_text")
        if not ok:
            failures.append(f"Orchestrator audio not playable: {detail}")
        if view.tts_provider != "sarvam":
            failures.append(f"Orchestrator tts_provider={view.tts_provider}, expected sarvam")

        # Streaming cascade — audio chunks must arrive before stream_end
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
        stream_first_audio = st.get("first_audio_ms")
        stream_total = st.get("total_ms")
        audio_idx = next(
            (i for i, e in enumerate(stream_events) if e.get("event") == "audio_chunk"),
            None,
        )
        end_idx = next(
            (i for i, e in enumerate(stream_events) if e.get("event") == "stream_end"),
            None,
        )
        print(
            "STREAM ORCH "
            f"events={names} "
            f"first_audio={stream_first_audio} total={stream_total} "
            f"transport={end.get('transport')} fallback={end.get('fallback_used')} "
            f"audio_chunks={sum(1 for e in stream_events if e.get('event') == 'audio_chunk')}"
        )
        if not stream_events or stream_events[0].get("event") != "stream_start":
            failures.append("Stream path missing stream_start")
        if "audio_chunk" not in names:
            failures.append("Stream path missing audio_chunk")
        if end.get("event") != "stream_end":
            failures.append("Stream path missing stream_end")
        if stream_first_audio is None:
            failures.append("Stream path missing first_audio_ms")
        if audio_idx is not None and end_idx is not None and audio_idx >= end_idx:
            failures.append("Transcript/audio sync: audio_chunk arrived after stream_end")
        if "stream_start" in names and "audio_chunk" in names and "stream_end" in names:
            if names.index("stream_start") < names.index("audio_chunk") < names.index(
                "stream_end"
            ):
                print("ANNOTATION WINDOWS OK: stream_start -> audio_chunk -> stream_end")
            else:
                failures.append("Annotation window order incorrect")

        # Warm path
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
            f"transport={(view2.provider_meta or {}).get('tts_transport')}"
        )

        # Outbound call audio path: WAV → Twilio μ-law
        if view.audio_base64:
            mulaw = pcm_or_wav_to_mulaw(
                base64.b64decode(view.audio_base64),
                src_sample_rate=settings.tts_sample_rate,
                is_wav=True,
            )
            print(f"TWILIO MULAW OK bytes={len(mulaw)} (outbound media-stream ready)")
            if len(mulaw) < 100:
                failures.append("Twilio mulaw conversion produced too little audio")
    except Exception as exc:  # noqa: BLE001
        msg = f"ORCH FAIL: {type(exc).__name__}: {exc}"
        print(msg)
        failures.append(msg)
    finally:
        store.clear()

    # Latency breakdown
    print("\n=== Latency breakdown (ms) ===")
    rows = [
        ("provider_init_ms", provider_init_ms),
        ("llm_ms", getattr(llm, "latency_ms", None) if llm else None),
        ("tts_ms", getattr(tts_en, "latency_ms", None) if tts_en else None),
        ("tts_first_audio_ms", (tts_en.meta or {}).get("first_audio_ms") if tts_en else None),
        ("orch_rag_ms", agg_timings.get("rag_ms")),
        ("orch_llm_ms", agg_timings.get("llm_ms")),
        ("orch_tts_ms", agg_timings.get("tts_ms")),
        ("orch_first_audio_ms", agg_timings.get("first_audio_ms")),
        ("orch_total_ms", agg_timings.get("total_ms")),
        ("stream_first_audio_ms", stream_first_audio),
        ("stream_total_ms", stream_total),
    ]
    for name, value in rows:
        flag_key = {
            "provider_init_ms": "provider_init_ms",
            "llm_ms": "llm_ms",
            "tts_ms": "tts_ms",
            "tts_first_audio_ms": "first_audio_ms",
            "orch_rag_ms": "provider_init_ms",
            "orch_llm_ms": "llm_ms",
            "orch_tts_ms": "tts_ms",
            "orch_first_audio_ms": "first_audio_ms",
            "orch_total_ms": "total_turn_ms",
            "stream_first_audio_ms": "first_audio_ms",
            "stream_total_ms": "total_turn_ms",
        }[name]
        compare_key = {
            "tts_ms": "tts_ms",
            "tts_first_audio_ms": "first_audio_ms",
            "orch_first_audio_ms": "first_audio_ms",
            "orch_total_ms": "total_turn_ms",
            "stream_first_audio_ms": "first_audio_ms",
            "stream_total_ms": "total_turn_ms",
        }.get(name)
        cmp = _compare(compare_key, value) if compare_key else "-"
        print(
            f"  {name:24} {value if value is not None else '—'!s:>10}  "
            f"[{_flag(flag_key, value)}]  {cmp}"
        )

    suggestions: list[str] = []
    if tts_en and (tts_en.latency_ms or 0) > SLOW_FLAGS["tts_ms"]:
        suggestions.append(
            "TTS slow: keep SARVAM_TTS_STREAMING=true and short reply payloads; "
            "HTTP fallback is slower than WebSocket streaming."
        )
    if stream_first_audio and stream_first_audio > SLOW_FLAGS["first_audio_ms"]:
        suggestions.append(
            "First audio slow: rely on stream_audio_from_texts (sentence cascade) "
            "and avoid waiting for full LLM completion before TTS."
        )
    if agg_timings.get("total_ms") and agg_timings["total_ms"] > SLOW_FLAGS["total_turn_ms"]:
        suggestions.append(
            "Total turn slow: check Groq latency and TTS in parallel; "
            "reduce llm_max_tokens for shorter spoken replies."
        )
    if suggestions:
        print("\n=== Suggestions ===")
        for s in suggestions:
            print(f"  - {s}")

    if failures:
        print("\n=== SMOKE FAILED ===")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("\n=== SMOKE PASSED ===")
    print("Demo readiness: YES — Sarvam STT + Sarvam TTS active; UI contract unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
