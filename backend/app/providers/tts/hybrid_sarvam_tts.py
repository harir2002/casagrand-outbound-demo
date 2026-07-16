"""Hybrid Sarvam TTS: WebSocket streaming with HTTP REST fallback."""

from __future__ import annotations

from app.core.logging import get_logger
from app.models.session import Language
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
