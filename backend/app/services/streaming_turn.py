"""End-to-end streaming turn helpers (Groq text → Sarvam TTS → client events)."""

from __future__ import annotations

import asyncio
import base64
import time
from collections.abc import AsyncIterator
from typing import Any

from app.core.logging import get_logger
from app.models.session import Language
from app.providers.stream_events import stream_event
from app.providers.types import LlmResult, SynthesisResult
from app.services.sentence_buffer import pop_complete_sentences

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "Casagrand voice assistant. Rephrase only; no new facts. Max 2 short sentences."
)


async def iter_speech_segments(
    *,
    llm,
    grounded_answer: str,
    user_text: str,
    language: Language,
    project_id: str,
    bucket: str,
    skip_llm: bool,
    on_text_delta,
    event_queue: asyncio.Queue,
) -> tuple[str, LlmResult | None, float, list[str]]:
    """Push speakable segments into event_queue as ('speech', text).

    Also emits text_delta events via on_text_delta. Returns polished text + llm meta.
    """
    warnings: list[str] = []
    if skip_llm or not grounded_answer.strip():
        speech = grounded_answer.strip() or "How can I help with this Casagrand project?"
        await event_queue.put(("speech", speech))
        await event_queue.put(("speech_done", None))
        return speech, None, 0.0, warnings

    prompt = (
        f"lang={language.value} project={project_id} bucket={bucket}\n"
        f"user={user_text}\n"
        f"ANSWER:\n{grounded_answer}\n"
        "Rewrite for speech only."
    )
    started = time.perf_counter()
    parts: list[str] = []
    buffer = ""
    first_token_ms: float | None = None
    try:
        async for delta in llm.stream_text(
            prompt, language, system_prompt=SYSTEM_PROMPT
        ):
            if first_token_ms is None:
                first_token_ms = round((time.perf_counter() - started) * 1000, 2)
            parts.append(delta)
            await on_text_delta(delta)
            buffer += delta
            ready, buffer = pop_complete_sentences(buffer)
            for sentence in ready:
                await event_queue.put(("speech", sentence))
        if buffer.strip():
            await event_queue.put(("speech", buffer.strip()))
        polished = "".join(parts).strip() or grounded_answer
        llm_ms = round((time.perf_counter() - started) * 1000, 2)
        result = LlmResult(
            text=polished,
            provider=getattr(llm, "name", "llm"),
            latency_ms=llm_ms,
            meta={
                "streaming": True,
                "first_token_ms": first_token_ms,
            },
        )
        await event_queue.put(("speech_done", None))
        return polished, result, llm_ms, warnings
    except Exception as exc:  # noqa: BLE001
        logger.warning("llm_stream_cascade_fallback error=%s", exc)
        warnings.append(f"LLM stream failed; speaking grounded FAQ ({exc})")
        llm_ms = round((time.perf_counter() - started) * 1000, 2)
        await event_queue.put(("speech", grounded_answer.strip()))
        await event_queue.put(("speech_done", None))
        return grounded_answer, None, llm_ms, warnings


async def speech_text_iterator(event_queue: asyncio.Queue) -> AsyncIterator[str]:
    while True:
        kind, payload = await event_queue.get()
        if kind == "speech_done":
            break
        if kind == "speech" and payload:
            yield str(payload)


def aggregate_pcm_to_synthesis(
    *,
    text: str,
    pcm_parts: list[bytes],
    wav_chunks: list[str],
    provider: str,
    transport: str,
    fallback_used: bool,
    stream_start_ms: float | None,
    first_audio_ms: float | None,
    latency_ms: float,
) -> SynthesisResult:
    audio_base64 = None
    if pcm_parts:
        from app.providers.tts.sarvam_tts_ws import pcm_chunks_to_wav_base64

        audio_base64 = pcm_chunks_to_wav_base64(b"".join(pcm_parts))
    elif wav_chunks:
        # HTTP fallback often returns a single full WAV already.
        audio_base64 = wav_chunks[0]

    return SynthesisResult(
        text=text,
        audio_base64=audio_base64,
        mime_type="audio/wav",
        provider=provider,
        latency_ms=latency_ms,
        meta={
            "transport": transport,
            "streaming": transport == "websocket",
            "fallback_used": fallback_used,
            "stream_start_ms": stream_start_ms,
            "first_audio_ms": first_audio_ms,
            "chunks": len(wav_chunks),
        },
    )


def decode_wav_pcm(audio_base64: str) -> bytes | None:
    """Best-effort extract PCM from a WAV base64 blob; None if not WAV."""
    try:
        raw = base64.b64decode(audio_base64)
    except Exception:  # noqa: BLE001
        return None
    if len(raw) > 44 and raw[:4] == b"RIFF":
        return raw[44:]
    return raw
