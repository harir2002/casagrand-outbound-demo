from app.models.session import Language
from app.providers.base import (
    LLMProvider,
    LlmResult,
    STTProvider,
    SynthesisResult,
    TranscriptResult,
    TTSProvider,
)


class MockSTT(STTProvider):
    async def transcribe(
        self, audio_bytes: bytes, language: Language | None = None
    ) -> TranscriptResult:
        return TranscriptResult(text="", language=language, confidence=0.0)


class MockTTS(TTSProvider):
    async def synthesize(self, text: str, language: Language) -> SynthesisResult:
        return SynthesisResult(audio_url=None, text=text, provider="mock")


class MockLLM(LLMProvider):
    async def complete(self, prompt: str, language: Language) -> LlmResult:
        return LlmResult(text=prompt, provider="mock")


def build_providers(
    stt: str, tts: str, llm: str
) -> tuple[STTProvider, TTSProvider, LLMProvider]:
    _ = (stt, tts, llm)
    return MockSTT(), MockTTS(), MockLLM()
