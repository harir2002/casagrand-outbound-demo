import base64
import time

from app.models.session import Language
from app.providers.tts.base import TTSProvider
from app.providers.types import SynthesisResult


class MockTTS(TTSProvider):
    name = "mock"

    async def synthesize(self, text: str, language: Language) -> SynthesisResult:
        started = time.perf_counter()
        # Deterministic placeholder WAV-like payload for local demos/tests.
        payload = f"MOCK_AUDIO:{language.value}:{text}".encode("utf-8")
        encoded = base64.b64encode(payload).decode("ascii")
        return SynthesisResult(
            text=text,
            audio_base64=encoded,
            audio_url=None,
            mime_type="audio/wav",
            provider=self.name,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            meta={"bytes": len(payload)},
        )
