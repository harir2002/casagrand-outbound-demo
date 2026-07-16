"""Groq LLM adapter for llama-3.1-8b-instant (OpenAI-compatible chat API)."""

from __future__ import annotations

import json
import time

import httpx

from app.core.logging import get_logger
from app.models.session import Language
from app.providers.http_client import create_async_client
from app.providers.llm.base import LLMProvider
from app.providers.types import LlmResult

logger = get_logger(__name__)


class GroqLLM(LLMProvider):
    name = "groq"

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.groq.com/openai/v1",
        model: str = "llama-3.1-8b-instant",
        temperature: float = 0.2,
        max_tokens: int = 120,
        timeout_seconds: float = 20.0,
        max_retries: int = 1,
        streaming: bool = True,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.streaming = streaming
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = create_async_client(self.timeout_seconds)
        return self._client

    async def aclose(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
        self._client = None

    async def complete(
        self,
        prompt: str,
        language: Language,
        *,
        system_prompt: str | None = None,
    ) -> LlmResult:
        if self.streaming:
            try:
                return await self._complete_streaming(
                    prompt, language, system_prompt=system_prompt
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("groq_stream_fallback_to_http error=%s", exc)
        return await self._complete_non_streaming(
            prompt, language, system_prompt=system_prompt
        )

    async def _complete_non_streaming(
        self,
        prompt: str,
        language: Language,
        *,
        system_prompt: str | None = None,
    ) -> LlmResult:
        started = time.perf_counter()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        last_error: Exception | None = None
        client = self._get_client()
        for attempt in range(self.max_retries + 1):
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=body,
                )
                response.raise_for_status()
                payload = response.json()

                choices = payload.get("choices") or []
                text = ""
                if choices:
                    text = (choices[0].get("message") or {}).get("content") or ""

                return LlmResult(
                    text=str(text).strip(),
                    provider=self.name,
                    latency_ms=round((time.perf_counter() - started) * 1000, 2),
                    meta={
                        "model": self.model,
                        "attempt": attempt,
                        "language": language.value,
                        "reused_client": True,
                        "streaming": False,
                    },
                )
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning("groq_llm_attempt_failed attempt=%s error=%s", attempt, exc)

        raise RuntimeError(f"Groq LLM failed: {last_error}")

    async def _complete_streaming(
        self,
        prompt: str,
        language: Language,
        *,
        system_prompt: str | None = None,
    ) -> LlmResult:
        """SSE chat completion — records first_token_ms; returns full text."""
        started = time.perf_counter()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": True,
        }

        client = self._get_client()
        parts: list[str] = []
        first_token_ms: float | None = None

        async with client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=body,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                try:
                    chunk = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                delta = (choices[0].get("delta") or {}).get("content") or ""
                if not delta:
                    continue
                if first_token_ms is None:
                    first_token_ms = round((time.perf_counter() - started) * 1000, 2)
                parts.append(str(delta))

        text = "".join(parts).strip()
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        return LlmResult(
            text=text,
            provider=self.name,
            latency_ms=latency_ms,
            meta={
                "model": self.model,
                "language": language.value,
                "reused_client": True,
                "streaming": True,
                "first_token_ms": first_token_ms,
            },
        )
