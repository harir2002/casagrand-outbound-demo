import base64
import time

from app.models.session import Language
from app.providers.stt.base import STTProvider
from app.providers.types import TranscriptResult


class MockSTT(STTProvider):
    name = "mock"

    def __init__(self, default_text: str = "Tell me about this project") -> None:
        self.default_text = default_text

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: Language | None = None,
        *,
        mime_type: str = "audio/wav",
    ) -> TranscriptResult:
        started = time.perf_counter()
        # Deterministic: if payload encodes UTF-8 "text:", use that; else default.
        text = self.default_text
        if audio_bytes.startswith(b"text:"):
            text = audio_bytes[5:].decode("utf-8", errors="ignore").strip() or text
        elif audio_bytes:
            # Placeholder decode for simulated audio payloads used in tests.
            try:
                decoded = base64.b64decode(audio_bytes, validate=False)
                if decoded.startswith(b"text:"):
                    text = decoded[5:].decode("utf-8", errors="ignore").strip() or text
            except Exception:
                pass

        return TranscriptResult(
            text=text,
            language=language,
            confidence=0.99,
            provider=self.name,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            meta={"mime_type": mime_type, "bytes": len(audio_bytes)},
        )
