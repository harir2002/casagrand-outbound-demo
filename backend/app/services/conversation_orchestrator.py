"""Real-mode conversation orchestrator: STT → domain → (LLM ∥ TTS)."""

from __future__ import annotations

import asyncio
import time

from fastapi import HTTPException

from app.core.logging import get_logger
from app.models.call_view import CallViewResponse, TurnRequest
from app.models.session import Language, UtteranceRequest
from app.providers.errors import ProviderConfigError, ProviderRuntimeError
from app.providers.factory import ProviderBundle, build_provider_bundle
from app.providers.types import LlmResult
from app.services import call_service
from app.services.audio_pipeline import AudioPipeline, SynthesizeOutcome
from app.services.fallback_service import text_only_fallback
from app.services.response_builder import build_provider_call_view

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

        parallel_started = time.perf_counter()
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
        _ = parallel_started
        warnings.extend(llm_warnings)
        if tts_outcome.warning:
            warnings.append(tts_outcome.warning)

        if session_result.reply and polished:
            session_result.reply.text = polished
            if session_result.session.transcript:
                last = session_result.session.transcript[-1]
                if last.role == "agent":
                    last.text = polished

        total_ms = round((time.perf_counter() - started) * 1000, 2)
        tts_meta = dict(tts_outcome.synthesis.meta or {})
        tts_first_audio = tts_meta.get("first_audio_ms")
        tts_stream_start = tts_meta.get("stream_start_ms")
        # Turn-relative: TTS starts after STT + domain (parallel with LLM).
        prefix_ms = stt_ms + domain_ms
        first_audio_ms = (
            round(prefix_ms + float(tts_first_audio), 2)
            if tts_first_audio is not None
            else round(prefix_ms + tts_outcome.latency_ms, 2)
        )
        stream_start_ms = (
            round(prefix_ms + float(tts_stream_start), 2)
            if tts_stream_start is not None
            else None
        )
        llm_first_token = (llm_result.meta or {}).get("first_token_ms") if llm_result else None

        logger.info(
            "orchestrator_turn mode=%s session=%s stt=%.1f domain=%.1f "
            "llm=%.1f tts=%.1f first_audio=%.1f parallel_wall=%.1f total=%.1f "
            "tts_transport=%s tts_fallback=%s",
            self.bundle.mode,
            payload.session_id,
            stt_ms,
            domain_ms,
            llm_ms,
            tts_outcome.latency_ms,
            first_audio_ms,
            parallel_wall_ms,
            total_ms,
            tts_meta.get("transport", "http"),
            bool(tts_meta.get("fallback_used")),
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
                "optimization": "parallel_llm_tts_grounded_audio",
                "tts_source": "grounded_faq",
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
            speech = grounded_answer.strip() or "How can I help with this Casagrand project?"
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
