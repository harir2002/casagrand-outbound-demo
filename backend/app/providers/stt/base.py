from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.models.session import Language
from app.providers.types import TranscriptResult


class STTProvider(ABC):
    name: str = "stt"

    @abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        language: Language | None = None,
        *,
        mime_type: str = "audio/wav",
    ) -> TranscriptResult:
        raise NotImplementedError

    async def transcribe_stream(
        self,
        audio_chunks: AsyncIterator[bytes],
        language: Language | None = None,
        *,
        mime_type: str = "audio/wav",
    ) -> TranscriptResult:
        """Default streaming path buffers chunks then calls transcribe()."""
        chunks: list[bytes] = []
        async for chunk in audio_chunks:
            if chunk:
                chunks.append(chunk)
        return await self.transcribe(b"".join(chunks), language, mime_type=mime_type)
