"""Hybrid Sarvam TTS: WebSocket streaming with HTTP REST fallback."""

from __future__ import annotations

from collections.abc import AsyncIterator

from app.core.logging import get_logger
from app.models.session import Language
from app.providers.stream_events import AudioChunk
from app.providers.tts.base import TTSProvider
from app.providers.tts.sarvam_tts import SarvamTTS
from app.providers.tts.sarvam_tts_ws import SarvamStreamingTTS
from app.providers.types import SynthesisResult

logger = get_logger(__name__)


class HybridSarvamTTS(TTSProvider):
    """Prefer WS streaming; fall back to the existing HTTP TTS path."""

    name = "sarvam"

    def __init__(
        self,
        http: SarvamTTS,
        streaming: SarvamStreamingTTS | None = None,
        *,
        prefer_streaming: bool = True,
    ) -> None:
        self.http = http
        self.streaming = streaming
        self.prefer_streaming = prefer_streaming and streaming is not None

    async def aclose(self) -> None:
        close = getattr(self.http, "aclose", None)
        if close is not None:
            await close()

    async def synthesize(self, text: str, language: Language) -> SynthesisResult:
        if self.prefer_streaming and self.streaming is not None:
            try:
                return await self.streaming.synthesize(text, language)
            except Exception as exc:  # noqa: BLE001
                logger.warning("sarvam_tts_ws_fallback_to_http error=%s", exc)
                result = await self.http.synthesize(text, language)
                meta = dict(result.meta or {})
                meta.update(
                    {
                        "transport": "http",
                        "streaming": False,
                        "fallback_used": True,
                        "stream_error": str(exc),
                        "first_audio_ms": result.latency_ms,
                        "stream_start_ms": None,
                    }
                )
                result.meta = meta
                return result

        result = await self.http.synthesize(text, language)
        meta = dict(result.meta or {})
        meta.setdefault("transport", "http")
        meta.setdefault("streaming", False)
        meta.setdefault("fallback_used", False)
        meta.setdefault("first_audio_ms", result.latency_ms)
        meta.setdefault("stream_start_ms", None)
        result.meta = meta
        return result

    async def stream_audio_chunks(
        self, text: str, language: Language
    ) -> AsyncIterator[AudioChunk]:
        if self.prefer_streaming and self.streaming is not None:
            try:
                async for chunk in self.streaming.stream_audio_chunks(text, language):
                    yield chunk
                return
            except Exception as exc:  # noqa: BLE001
                logger.warning("sarvam_tts_ws_chunk_fallback_to_http error=%s", exc)
                result = await self.http.synthesize(text, language)
                if result.audio_base64:
                    yield AudioChunk(
                        audio_base64=result.audio_base64,
                        mime_type=result.mime_type or "audio/wav",
                        index=0,
                        meta={
                            "transport": "http",
                            "streaming": False,
                            "fallback_used": True,
                            "stream_error": str(exc),
                            "first_audio_ms": result.latency_ms,
                        },
                    )
                return

        async for chunk in super().stream_audio_chunks(text, language):
            chunk.meta.setdefault("transport", "http")
            chunk.meta.setdefault("fallback_used", False)
            yield chunk

    async def stream_audio_from_texts(
        self, texts: AsyncIterator[str], language: Language
    ) -> AsyncIterator[AudioChunk]:
        if self.prefer_streaming and self.streaming is not None:
            buffered: list[str] = []

            async def _tee() -> AsyncIterator[str]:
                async for piece in texts:
                    cleaned = (piece or "").strip()
                    if cleaned:
                        buffered.append(cleaned)
                        yield cleaned

            try:
                async for chunk in self.streaming.stream_audio_from_texts(
                    _tee(), language
                ):
                    yield chunk
                return
            except Exception as exc:  # noqa: BLE001
                logger.warning("sarvam_tts_ws_segment_fallback_to_http error=%s", exc)
                joined = " ".join(buffered).strip()
                if not joined:
                    return
                result = await self.http.synthesize(joined, language)
                if result.audio_base64:
                    yield AudioChunk(
                        audio_base64=result.audio_base64,
                        mime_type=result.mime_type or "audio/wav",
                        index=0,
                        meta={
                            "transport": "http",
                            "streaming": False,
                            "fallback_used": True,
                            "stream_error": str(exc),
                            "first_audio_ms": result.latency_ms,
                        },
                    )
                return

        async for chunk in super().stream_audio_from_texts(texts, language):
            yield chunk
