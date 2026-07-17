"""Test-only provider doubles. Not used by the live demo path."""

from __future__ import annotations

import base64
import time

from app.models.session import Language
from app.providers.llm.base import LLMProvider
from app.providers.stt.base import STTProvider
from app.providers.tts.base import TTSProvider
from app.providers.types import LlmResult, SynthesisResult, TranscriptResult


class StubSTT(STTProvider):
    name = "stub"

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
        text = self.default_text
        if audio_bytes.startswith(b"text:"):
            text = audio_bytes[5:].decode("utf-8", errors="ignore").strip() or text
        return TranscriptResult(
            text=text,
            language=language,
            confidence=0.99,
            provider=self.name,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            meta={"mime_type": mime_type, "bytes": len(audio_bytes)},
        )


class StubTTS(TTSProvider):
    name = "stub"

    async def synthesize(self, text: str, language: Language) -> SynthesisResult:
        started = time.perf_counter()
        payload = f"STUB_AUDIO:{language.value}:{text}".encode("utf-8")
        encoded = base64.b64encode(payload).decode("ascii")
        return SynthesisResult(
            text=text,
            audio_base64=encoded,
            audio_url=None,
            mime_type="audio/wav",
            provider=self.name,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            meta={
                "bytes": len(payload),
                "transport": "stub",
                "streaming": False,
                "fallback_used": False,
                "first_audio_ms": 1.0,
                "stream_start_ms": 0.5,
            },
        )

    async def stream_audio_from_texts(self, texts, language: Language):
        """Synthesize each speech segment so cascade tests get ordered chunks."""
        from app.providers.stream_events import AudioChunk

        index = 0
        async for piece in texts:
            cleaned = (piece or "").strip()
            if not cleaned:
                continue
            result = await self.synthesize(cleaned, language)
            meta = dict(result.meta or {})
            meta["streaming"] = True
            meta["transport"] = "stub"
            yield AudioChunk(
                audio_base64=result.audio_base64 or "",
                mime_type=result.mime_type or "audio/wav",
                index=index,
                meta=meta,
            )
            index += 1


class StubLLM(LLMProvider):
    name = "stub"

    async def complete(
        self,
        prompt: str,
        language: Language,
        *,
        system_prompt: str | None = None,
    ) -> LlmResult:
        started = time.perf_counter()
        text = prompt.strip()
        if "GROUNDED_ANSWER:" in text:
            text = text.split("GROUNDED_ANSWER:", 1)[1].strip()
        elif "ANSWER:" in text:
            text = text.split("ANSWER:", 1)[1].strip()
            if "Rewrite for speech only." in text:
                text = text.split("Rewrite for speech only.", 1)[0].strip()
        return LlmResult(
            text=text,
            provider=self.name,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            meta={
                "language": language.value,
                "has_system": bool(system_prompt),
                "streaming": False,
            },
        )

    async def stream_text(
        self,
        prompt: str,
        language: Language,
        *,
        system_prompt: str | None = None,
    ):
        result = await self.complete(
            prompt, language, system_prompt=system_prompt
        )
        words = result.text.split()
        if not words:
            return
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")


class FailingSTT(STTProvider):
    name = "failing-stt"

    async def transcribe(self, audio_bytes: bytes, language: Language | None = None, *, mime_type: str = "audio/wav") -> TranscriptResult:
        raise RuntimeError("simulated STT outage")


class FailingTTS(TTSProvider):
    name = "failing-tts"

    async def synthesize(self, text: str, language: Language) -> SynthesisResult:
        raise RuntimeError("simulated TTS outage")


class FailingLLM(LLMProvider):
    name = "failing-llm"

    async def complete(
        self,
        prompt: str,
        language: Language,
        *,
        system_prompt: str | None = None,
    ) -> LlmResult:
        raise RuntimeError("simulated LLM outage")
