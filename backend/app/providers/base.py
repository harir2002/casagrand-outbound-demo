from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.models.session import Language


@dataclass
class TranscriptResult:
    text: str
    language: Language | None = None
    confidence: float = 1.0


@dataclass
class SynthesisResult:
    audio_url: str | None
    text: str
    provider: str


@dataclass
class LlmResult:
    text: str
    provider: str


class STTProvider(ABC):
    @abstractmethod
    async def transcribe(
        self, audio_bytes: bytes, language: Language | None = None
    ) -> TranscriptResult:
        raise NotImplementedError


class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str, language: Language) -> SynthesisResult:
        raise NotImplementedError


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, language: Language) -> LlmResult:
        raise NotImplementedError
