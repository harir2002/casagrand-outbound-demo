"""Real-mode conversation orchestrator: STT → domain → (LLM ∥ TTS) + stream path."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from typing import Any

from fastapi import HTTPException

from app.core.logging import get_logger
from app.models.call_view import CallViewResponse, TurnRequest
from app.models.session import Language, UtteranceRequest
from app.providers.errors import ProviderConfigError, ProviderRuntimeError
from app.providers.factory import ProviderBundle, build_provider_bundle
from app.providers.stream_events import stream_event
from app.providers.types import LlmResult
from app.services import call_service
from app.services.audio_pipeline import AudioPipeline, SynthesizeOutcome
from app.services.fallback_service import text_only_fallback
from app.services.response_builder import build_provider_call_view
from app.services.streaming_turn import (
    aggregate_pcm_to_synthesis,
    decode_wav_pcm,
    iter_speech_segments,
    speech_text_iterator,
)

logger = get_logger(__name__)

SYSTEM_PROMPT = (
    "Casagrand voice assistant. Rephrase only; no new facts. Max 2 short sentences."
)


class ConversationOrchestrator:
    def __init__(self, bundle: ProviderBundle) -> None:
        self.bundle = bundle
        self.audio = AudioPipeline(self.bundle)

    async def handle_turn(self, payload: TurnRequest) -> CallViewResponse:
        started = time.perf_counter()
        warnings: list[str] = []

        try:
            stt_outcome = await self.audio.maybe_transcribe(
                text=payload.text,
                audio_base64=payload.audio_base64,
                language=payload.language,
                mime_type=payload.audio_mime_type or "audio/wav",
            )
        except ProviderRuntimeError as exc:
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Speech recognition unavailable ({exc}). "
                    "Please retry with typed text or try again shortly."
                ),
            ) from exc

        user_text = stt_outcome.text
        transcript = stt_outcome.transcript
        stt_ms = stt_outcome.latency_ms
        if stt_outcome.warning:
            warnings.append(stt_outcome.warning)

        domain_started = time.perf_counter()
        session_result = call_service.process_utterance(
            payload.session_id,
            UtteranceRequest(
                text=user_text,
                language=payload.language,
                interrupt=payload.interrupt,
            ),
        )
        domain_ms = round((time.perf_counter() - domain_started) * 1000, 2)

        grounded = session_result.reply.text if session_result.reply else ""
        language = session_result.session.language

        polished, llm_result, llm_warnings, llm_ms, tts_outcome, parallel_wall_ms = (
            await self._parallel_polish_and_tts(
                grounded_answer=grounded,
                user_text=user_text,
                language=language,
                project_id=session_result.session.project_id,
                bucket=session_result.session.flow_bucket.value,
                skip_llm=payload.skip_llm,
            )
        )
        warnings.extend(llm_warnings)
        if tts_outcome.warning:
            warnings.append(tts_outcome.warning)

        if session_result.reply and polished:
            session_result.reply.text = polished
            if session_result.session.transcript:
                last = session_result.session.transcript[-1]
                if last.role == "agent":
                    last.text = polished

        return self._build_turn_response(
            session_result=session_result,
            transcript=transcript,
            tts_outcome=tts_outcome,
            llm_result=llm_result,
            warnings=warnings,
            stt_ms=stt_ms,
            domain_ms=domain_ms,
            llm_ms=llm_ms,
            parallel_wall_ms=parallel_wall_ms,
            started=started,
            optimization="parallel_llm_tts_grounded_audio",
            tts_source="grounded_faq",
        )

    async def handle_turn_stream(
        self, payload: TurnRequest
    ) -> AsyncIterator[dict[str, Any]]:
        """NDJSON-friendly event stream: start → text/audio chunks → end."""
        started = time.perf_counter()
        warnings: list[str] = []

        try:
            stt_outcome = await self.audio.maybe_transcribe(
                text=payload.text,
                audio_base64=payload.audio_base64,
                language=payload.language,
                mime_type=payload.audio_mime_type or "audio/wav",
            )
        except ProviderRuntimeError as exc:
            yield stream_event(
                "error",
                message=(
                    f"Speech recognition unavailable ({exc}). "
                    "Please retry with typed text or try again shortly."
                ),
                code=503,
            )
            return

        user_text = stt_outcome.text
        transcript = stt_outcome.transcript
        stt_ms = stt_outcome.latency_ms
        if stt_outcome.warning:
            warnings.append(stt_outcome.warning)

        domain_started = time.perf_counter()
        session_result = call_service.process_utterance(
            payload.session_id,
            UtteranceRequest(
                text=user_text,
                language=payload.language,
                interrupt=payload.interrupt,
            ),
        )
        domain_ms = round((time.perf_counter() - domain_started) * 1000, 2)
        grounded = session_result.reply.text if session_result.reply else ""
        language = session_result.session.language
        bucket = session_result.session.flow_bucket.value
        project_id = session_result.session.project_id

        stream_start_ms = round((time.perf_counter() - started) * 1000, 2)
        yield stream_event(
            "stream_start",
            session_id=payload.session_id,
            bucket=bucket,
            intent=(session_result.reply.intent.value if session_result.reply else (session_result.session.last_intent.value if session_result.session.last_intent else None)),
            response_text=grounded,
            transport="websocket",
            fallback_used=False,
            timings={
                "stt_ms": stt_ms,
                "domain_ms": domain_ms,
                "stream_start_ms": stream_start_ms,
            },
        )

        try:
            async for event in self._cascade_stream(
                session_result=session_result,
                transcript=transcript,
                grounded=grounded,
                user_text=user_text,
                language=language,
                project_id=project_id,
                bucket=bucket,
                skip_llm=payload.skip_llm,
                warnings=warnings,
                stt_ms=stt_ms,
                domain_ms=domain_ms,
                started=started,
                stream_start_ms=stream_start_ms,
            ):
                yield event
        except Exception as exc:  # noqa: BLE001
            logger.warning("stream_cascade_failed_fallback_aggregated error=%s", exc)
            warnings.append(f"Streaming failed; using aggregated path ({exc})")
            polished, llm_result, llm_warnings, llm_ms, tts_outcome, parallel_wall_ms = (
                await self._parallel_polish_and_tts(
                    grounded_answer=grounded,
                    user_text=user_text,
                    language=language,
                    project_id=project_id,
                    bucket=bucket,
                    skip_llm=payload.skip_llm,
                )
            )
            warnings.extend(llm_warnings)
            if tts_outcome.warning:
                warnings.append(tts_outcome.warning)
            if session_result.reply and polished:
                session_result.reply.text = polished
                if session_result.session.transcript:
                    last = session_result.session.transcript[-1]
                    if last.role == "agent":
                        last.text = polished
            tts_meta = dict(tts_outcome.synthesis.meta or {})
            tts_meta["fallback_used"] = True
            tts_outcome.synthesis.meta = tts_meta
            view = self._build_turn_response(
                session_result=session_result,
                transcript=transcript,
                tts_outcome=tts_outcome,
                llm_result=llm_result,
                warnings=warnings,
                stt_ms=stt_ms,
                domain_ms=domain_ms,
                llm_ms=llm_ms,
                parallel_wall_ms=parallel_wall_ms,
                started=started,
                optimization="fallback_aggregated_after_stream_error",
                tts_source="grounded_faq",
            )
            if view.audio_base64:
                yield stream_event(
                    "audio_chunk",
                    audio_base64=view.audio_base64,
                    mime_type=view.audio_mime_type or "audio/wav",
                    index=0,
                )
            yield stream_event(
                "stream_end",
                call_view=view.model_dump(mode="json"),
                provider_meta=view.provider_meta,
                timings=(view.provider_meta or {}).get("timings") or {},
                transport=view.provider_meta.get("tts_transport", "http"),
                fallback_used=True,
                response_text=view.reply_text,
            )

    async def _cascade_stream(
        self,
        *,
        session_result,
        transcript,
        grounded: str,
        user_text: str,
        language: Language,
        project_id: str,
        bucket: str,
        skip_llm: bool,
        warnings: list[str],
        stt_ms: float,
        domain_ms: float,
        started: float,
        stream_start_ms: float,
    ) -> AsyncIterator[dict[str, Any]]:
        speech_q: asyncio.Queue = asyncio.Queue()
        text_q: asyncio.Queue = asyncio.Queue()
        pcm_parts: list[bytes] = []
        wav_chunks: list[str] = []
        client_first_audio_ms: float | None = None
        tts_stream_start_ms: float | None = None
        transport = "websocket"
        fallback_used = False
        tts_started = time.perf_counter()

        async def on_text_delta(delta: str) -> None:
            await text_q.put(delta)

        async def produce() -> tuple[str, LlmResult | None, float, list[str]]:
            return await iter_speech_segments(
                llm=self.bundle.llm,
                grounded_answer=grounded,
                user_text=user_text,
                language=language,
                project_id=project_id,
                bucket=bucket,
                skip_llm=skip_llm,
                on_text_delta=on_text_delta,
                event_queue=speech_q,
            )

        produce_task = asyncio.create_task(produce())

        async def pump_tts() -> None:
            nonlocal transport, fallback_used, tts_stream_start_ms
            async for chunk in self.bundle.tts.stream_audio_from_texts(
                speech_text_iterator(speech_q), language
            ):
                meta = chunk.meta or {}
                transport = str(meta.get("transport") or transport)
                fallback_used = bool(meta.get("fallback_used") or fallback_used)
                if tts_stream_start_ms is None and meta.get("stream_start_ms") is not None:
                    tts_stream_start_ms = float(meta["stream_start_ms"])
                wav_chunks.append(chunk.audio_base64)
                pcm = chunk.pcm_bytes or decode_wav_pcm(chunk.audio_base64)
                if pcm:
                    pcm_parts.append(pcm)
                await text_q.put(("audio", chunk))
            await text_q.put(("audio_done", None))

        tts_task = asyncio.create_task(pump_tts())

        try:
            while True:
                item = await text_q.get()
                if isinstance(item, tuple) and item[0] == "audio_done":
                    break
                if isinstance(item, tuple) and item[0] == "audio":
                    chunk = item[1]
                    if client_first_audio_ms is None:
                        client_first_audio_ms = round(
                            (time.perf_counter() - started) * 1000, 2
                        )
                    yield stream_event(
                        "audio_chunk",
                        audio_base64=chunk.audio_base64,
                        mime_type=chunk.mime_type,
                        index=chunk.index,
                        transport=transport,
                        fallback_used=fallback_used,
                    )
                elif isinstance(item, str):
                    yield stream_event("text_delta", text=item)
        finally:
            polished, llm_result, llm_ms, llm_warnings = await produce_task
            warnings.extend(llm_warnings)
            await tts_task

        tts_ms = round((time.perf_counter() - tts_started) * 1000, 2)
        if session_result.reply and polished:
            session_result.reply.text = polished
            if session_result.session.transcript:
                last = session_result.session.transcript[-1]
                if last.role == "agent":
                    last.text = polished

        synthesis = aggregate_pcm_to_synthesis(
            text=polished or grounded,
            pcm_parts=pcm_parts,
            wav_chunks=wav_chunks,
            provider=self.bundle.tts_name,
            transport=transport,
            fallback_used=fallback_used,
            stream_start_ms=tts_stream_start_ms,
            first_audio_ms=(
                None
                if client_first_audio_ms is None
                else round(max(client_first_audio_ms - stt_ms - domain_ms, 0), 2)
            ),
            latency_ms=tts_ms,
        )
        tts_outcome = SynthesizeOutcome(
            synthesis=synthesis,
            warning=None,
            latency_ms=tts_ms,
            degraded=False,
        )
        view = self._build_turn_response(
            session_result=session_result,
            transcript=transcript,
            tts_outcome=tts_outcome,
            llm_result=llm_result,
            warnings=warnings,
            stt_ms=stt_ms,
            domain_ms=domain_ms,
            llm_ms=llm_ms,
            parallel_wall_ms=tts_ms,
            started=started,
            optimization="cascade_llm_stream_tts_stream",
            tts_source="llm_polished" if llm_result else "grounded_faq",
            client_first_audio_ms=client_first_audio_ms,
            stream_start_override=stream_start_ms,
        )
        yield stream_event(
            "stream_end",
            call_view=view.model_dump(mode="json"),
            provider_meta=view.provider_meta,
            timings=(view.provider_meta or {}).get("timings") or {},
            transport=transport,
            fallback_used=fallback_used,
            response_text=view.reply_text,
            session_id=view.session_id,
            bucket=view.active_bucket,
            intent=view.last_intent,
        )

    def _build_turn_response(
        self,
        *,
        session_result,
        transcript,
        tts_outcome: SynthesizeOutcome,
        llm_result: LlmResult | None,
        warnings: list[str],
        stt_ms: float,
        domain_ms: float,
        llm_ms: float,
        parallel_wall_ms: float,
        started: float,
        optimization: str,
        tts_source: str,
        client_first_audio_ms: float | None = None,
        stream_start_override: float | None = None,
    ) -> CallViewResponse:
        total_ms = round((time.perf_counter() - started) * 1000, 2)
        tts_meta = dict(tts_outcome.synthesis.meta or {})
        tts_first_audio = tts_meta.get("first_audio_ms")
        tts_stream_start = tts_meta.get("stream_start_ms")
        prefix_ms = stt_ms + domain_ms
        if client_first_audio_ms is not None:
            first_audio_ms = client_first_audio_ms
        elif tts_first_audio is not None:
            first_audio_ms = round(prefix_ms + float(tts_first_audio), 2)
        else:
            first_audio_ms = round(prefix_ms + tts_outcome.latency_ms, 2)
        if stream_start_override is not None:
            stream_start_ms = stream_start_override
        elif tts_stream_start is not None:
            stream_start_ms = round(prefix_ms + float(tts_stream_start), 2)
        else:
            stream_start_ms = None
        llm_first_token = (
            (llm_result.meta or {}).get("first_token_ms") if llm_result else None
        )

        logger.info(
            "orchestrator_turn mode=%s session=%s stt=%.1f domain=%.1f "
            "llm=%.1f tts=%.1f first_audio=%.1f parallel_wall=%.1f total=%.1f "
            "tts_transport=%s tts_fallback=%s opt=%s",
            self.bundle.mode,
            session_result.session.session_id,
            stt_ms,
            domain_ms,
            llm_ms,
            tts_outcome.latency_ms,
            first_audio_ms,
            parallel_wall_ms,
            total_ms,
            tts_meta.get("transport", "http"),
            bool(tts_meta.get("fallback_used")),
            optimization,
        )

        return build_provider_call_view(
            session_result,
            transcript=transcript,
            synthesis=tts_outcome.synthesis,
            provider_meta={
                "mode": self.bundle.mode,
                "stt": self.bundle.stt_name,
                "tts": tts_outcome.synthesis.provider,
                "llm": llm_result.provider if llm_result else "skipped",
                "optimization": optimization,
                "tts_source": tts_source,
                "tts_transport": tts_meta.get("transport", "http"),
                "tts_streaming": bool(tts_meta.get("streaming")),
                "tts_fallback_used": bool(tts_meta.get("fallback_used")),
                "llm_streaming": bool((llm_result.meta or {}).get("streaming"))
                if llm_result
                else False,
                "timings": {
                    "stt_ms": stt_ms,
                    "domain_ms": domain_ms,
                    "llm_ms": llm_ms,
                    "llm_first_token_ms": llm_first_token,
                    "tts_ms": tts_outcome.latency_ms,
                    "stream_start_ms": stream_start_ms,
                    "first_audio_ms": first_audio_ms,
                    "parallel_wall_ms": parallel_wall_ms,
                    "total_ms": total_ms,
                },
                "degraded": tts_outcome.degraded,
            },
            warnings=warnings,
            stt_latency_ms=stt_ms,
            llm_latency_ms=llm_ms,
            tts_latency_ms=tts_outcome.latency_ms,
            total_latency_ms=total_ms,
        )

    async def _parallel_polish_and_tts(
        self,
        *,
        grounded_answer: str,
        user_text: str,
        language: Language,
        project_id: str,
        bucket: str,
        skip_llm: bool,
    ) -> tuple[str, LlmResult | None, list[str], float, SynthesizeOutcome, float]:
        """TTS grounded FAQ while LLM polishes in parallel (wall ≈ max)."""
        wall_started = time.perf_counter()

        if skip_llm or not grounded_answer.strip():
            speech = (
                grounded_answer.strip()
                or "How can I help with this Casagrand project?"
            )
            tts_outcome = await self.audio.synthesize(speech, language)
            wall_ms = round((time.perf_counter() - wall_started) * 1000, 2)
            return grounded_answer or speech, None, [], 0.0, tts_outcome, wall_ms

        polish_task = asyncio.create_task(
            self._maybe_polish(
                grounded_answer=grounded_answer,
                user_text=user_text,
                language=language,
                project_id=project_id,
                bucket=bucket,
                skip_llm=False,
            )
        )
        tts_task = asyncio.create_task(
            self.audio.synthesize(grounded_answer, language)
        )
        polish_result, tts_outcome = await asyncio.gather(polish_task, tts_task)
        polished, llm_result, llm_warnings, llm_ms = polish_result
        wall_ms = round((time.perf_counter() - wall_started) * 1000, 2)
        return polished, llm_result, llm_warnings, llm_ms, tts_outcome, wall_ms

    async def _maybe_polish(
        self,
        *,
        grounded_answer: str,
        user_text: str,
        language: Language,
        project_id: str,
        bucket: str,
        skip_llm: bool,
    ) -> tuple[str, LlmResult | None, list[str], float]:
        if skip_llm or not grounded_answer.strip():
            return grounded_answer, None, [], 0.0

        prompt = (
            f"lang={language.value} project={project_id} bucket={bucket}\n"
            f"user={user_text}\n"
            f"ANSWER:\n{grounded_answer}\n"
            "Rewrite for speech only."
        )
        started = time.perf_counter()
        warnings: list[str] = []
        try:
            result = await self.bundle.llm.complete(
                prompt,
                language,
                system_prompt=SYSTEM_PROMPT,
            )
            latency = round((time.perf_counter() - started) * 1000, 2)
            text = result.text.strip() or grounded_answer
            return text, result, warnings, latency
        except Exception as exc:  # noqa: BLE001
            latency = round((time.perf_counter() - started) * 1000, 2)
            fb = text_only_fallback(
                grounded_answer=grounded_answer,
                language=language,
                failed_provider="llm",
                error=str(exc),
            )
            warnings.append(fb.warning)
            return grounded_answer, None, warnings, latency


_orchestrator: ConversationOrchestrator | None = None


def get_orchestrator() -> ConversationOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        try:
            bundle = build_provider_bundle()
        except ProviderConfigError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        _orchestrator = ConversationOrchestrator(bundle)
    return _orchestrator


def reset_orchestrator() -> None:
    global _orchestrator
    _orchestrator = None
