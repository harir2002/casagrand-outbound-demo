from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.models.session import Language
from app.providers.types import LlmResult


class LLMProvider(ABC):
    name: str = "llm"

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        language: Language,
        *,
        system_prompt: str | None = None,
    ) -> LlmResult:
        raise NotImplementedError

    async def stream_text(
        self,
        prompt: str,
        language: Language,
        *,
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        """Yield text deltas. Default: single chunk from complete()."""
        result = await self.complete(
            prompt, language, system_prompt=system_prompt
        )
        if result.text:
            yield result.text
