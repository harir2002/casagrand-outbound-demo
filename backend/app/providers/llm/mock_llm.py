import time

from app.models.session import Language
from app.providers.llm.base import LLMProvider
from app.providers.types import LlmResult


class MockLLM(LLMProvider):
    name = "mock"

    async def complete(
        self,
        prompt: str,
        language: Language,
        *,
        system_prompt: str | None = None,
    ) -> LlmResult:
        started = time.perf_counter()
        # Keep FAQ-controlled text intact; mock only echoes grounded content.
        text = prompt.strip()
        if "GROUNDED_ANSWER:" in text:
            text = text.split("GROUNDED_ANSWER:", 1)[1].strip()
        return LlmResult(
            text=text,
            provider=self.name,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            meta={"language": language.value, "has_system": bool(system_prompt)},
        )
