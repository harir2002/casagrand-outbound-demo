from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.models.session import Language
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
