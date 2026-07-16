"""Provider adapter stubs for future Sarvam STT/TTS and Groq/OpenRouter LLM."""

from app.providers.base import (
    LLMProvider,
    LlmResult,
    STTProvider,
    SynthesisResult,
    TranscriptResult,
    TTSProvider,
)
from app.providers.mock import MockLLM, MockSTT, MockTTS, build_providers

__all__ = [
    "LLMProvider",
    "LlmResult",
    "STTProvider",
    "SynthesisResult",
    "TranscriptResult",
    "TTSProvider",
    "MockLLM",
    "MockSTT",
    "MockTTS",
    "build_providers",
]
