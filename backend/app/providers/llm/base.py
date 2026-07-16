from abc import ABC, abstractmethod

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
