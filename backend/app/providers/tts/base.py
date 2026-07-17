from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.models.session import Language
from app.providers.stream_events import AudioChunk
from app.providers.types import SynthesisResult


class TTSProvider(ABC):
    name: str = "tts"

    @abstractmethod
    async def synthesize(self, text: str, language: Language) -> SynthesisResult:
        raise NotImplementedError

    async def synthesize_stream(
        self, text: str, language: Language
    ) -> AsyncIterator[bytes]:
        """Default streaming yields a single audio chunk from synthesize()."""
        result = await self.synthesize(text, language)
        if result.audio_base64:
            import base64

            yield base64.b64decode(result.audio_base64)
        elif result.audio_url:
            yield result.audio_url.encode("utf-8")
        else:
            yield b""

    async def stream_audio_chunks(
        self, text: str, language: Language
    ) -> AsyncIterator[AudioChunk]:
        """Yield progressive audio pieces (WAV base64). Default: one chunk."""
        result = await self.synthesize(text, language)
        if result.audio_base64:
            yield AudioChunk(
                audio_base64=result.audio_base64,
                mime_type=result.mime_type or "audio/wav",
                index=0,
                meta=dict(result.meta or {}),
            )

    async def stream_audio_from_texts(
        self, texts: AsyncIterator[str], language: Language
    ) -> AsyncIterator[AudioChunk]:
        """Consume text segments and yield audio. Default: join then synthesize."""
        parts: list[str] = []
        async for piece in texts:
            cleaned = (piece or "").strip()
            if cleaned:
                parts.append(cleaned)
        if not parts:
            return
        async for chunk in self.stream_audio_chunks(" ".join(parts), language):
            yield chunk
