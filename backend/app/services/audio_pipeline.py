"""STT/TTS helpers for the live provider pipeline."""

from __future__ import annotations

import base64
import time
from dataclasses import dataclass

from app.core.logging import get_logger
from app.models.session import Language
from app.providers.errors import ProviderRuntimeError
from app.providers.factory import ProviderBundle
from app.providers.types import SynthesisResult, TranscriptResult
from app.services.fallback_service import synthesis_placeholder, text_only_fallback

logger = get_logger(__name__)


@dataclass
class TranscribeOutcome:
    text: str
    transcript: TranscriptResult | None
    warning: str | None
    latency_ms: float
    degraded: bool = False


@dataclass
class SynthesizeOutcome:
    synthesis: SynthesisResult
    warning: str | None
    latency_ms: float
    degraded: bool = False


class AudioPipeline:
    def __init__(self, bundle: ProviderBundle) -> None:
        self.bundle = bundle

    async def maybe_transcribe(
        self,
        *,
        text: str | None,
        audio_base64: str | None,
        language: Language | None,
        mime_type: str = "audio/wav",
    ) -> TranscribeOutcome:
        if text and text.strip():
            return TranscribeOutcome(
                text=text.strip(),
                transcript=None,
                warning=None,
                latency_ms=0.0,
            )
        if not audio_base64:
            raise ValueError("Either text or audio_base64 is required")

        audio_bytes = base64.b64decode(audio_base64)
        started = time.perf_counter()
        try:
            result = await self.bundle.stt.transcribe(
                audio_bytes, language, mime_type=mime_type
            )
            latency = round((time.perf_counter() - started) * 1000, 2)
            if not result.text.strip():
                raise ProviderRuntimeError("stt", "empty transcript")
            return TranscribeOutcome(
                text=result.text.strip(),
                transcript=result,
                warning=None,
                latency_ms=latency,
            )
        except Exception as exc:  # noqa: BLE001
            latency = round((time.perf_counter() - started) * 1000, 2)
            logger.warning("stt_runtime_failure error=%s", exc)
            lang = language or Language.EN
            fb = text_only_fallback(
                grounded_answer="",
                language=lang,
                failed_provider="stt",
                error=str(exc),
            )
            # Caller should abort turn or ask user to type; surface clear warning.
            raise ProviderRuntimeError("stt", fb.warning) from exc

    async def synthesize(self, text: str, language: Language) -> SynthesizeOutcome:
        started = time.perf_counter()
        try:
            result = await self.bundle.tts.synthesize(text, language)
            latency = round((time.perf_counter() - started) * 1000, 2)
            return SynthesizeOutcome(
                synthesis=result,
                warning=None,
                latency_ms=latency,
            )
        except Exception as exc:  # noqa: BLE001
            latency = round((time.perf_counter() - started) * 1000, 2)
            logger.warning("tts_runtime_failure error=%s", exc)
            fb = text_only_fallback(
                grounded_answer=text,
                language=language,
                failed_provider="tts",
                error=str(exc),
            )
            return SynthesizeOutcome(
                synthesis=synthesis_placeholder(fb.reply_text, language, "tts"),
                warning=fb.warning,
                latency_ms=latency,
                degraded=True,
            )
