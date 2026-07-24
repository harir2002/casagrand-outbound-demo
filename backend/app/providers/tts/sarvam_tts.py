"""Sarvam TTS adapter (REST HTTP). Used by HybridSarvamTTS as the reliable path."""

from __future__ import annotations

import time

import httpx

from app.core.logging import get_logger
from app.models.session import Language
from app.providers.http_client import create_async_client
from app.providers.tts.base import TTSProvider
from app.providers.types import SynthesisResult

logger = get_logger(__name__)

_LANG_MAP = {
    Language.EN: "en-IN",
    Language.TA: "ta-IN",
    Language.TANGLISH: "en-IN",
}

# Sarvam TTS is faster on concise utterances; keep domain facts intact.
_MAX_TTS_CHARS = 420


class SarvamTTS(TTSProvider):
    name = "sarvam"

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.sarvam.ai",
        model: str = "bulbul:v2",
        speaker: str = "anushka",
        timeout_seconds: float = 20.0,
        max_retries: int = 1,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.speaker = speaker
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = create_async_client(self.timeout_seconds)
        return self._client

    async def aclose(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
        self._client = None

    @staticmethod
    def _clip_for_speech(text: str) -> str:
        cleaned = " ".join(text.split())
        if len(cleaned) <= _MAX_TTS_CHARS:
            return cleaned
        clipped = cleaned[:_MAX_TTS_CHARS].rsplit(" ", 1)[0]
        return clipped or cleaned[:_MAX_TTS_CHARS]

    async def synthesize(self, text: str, language: Language) -> SynthesisResult:
        if not text.strip():
            raise ValueError("text is empty")

        started = time.perf_counter()
        speech_text = self._clip_for_speech(text)
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json",
        }
        body = {
            "text": speech_text,
            "target_language_code": _LANG_MAP.get(language, "en-IN"),
            "speaker": self.speaker,
            "model": self.model,
        }

        last_error: Exception | None = None
        client = self._get_client()
        for attempt in range(self.max_retries + 1):
            try:
                response = await client.post(
                    f"{self.base_url}/text-to-speech",
                    headers=headers,
                    json=body,
                )
                response.raise_for_status()
                payload = response.json()

                audio_base64 = None
                audio_url = None
                if isinstance(payload.get("audios"), list) and payload["audios"]:
                    audio_base64 = payload["audios"][0]
                elif payload.get("audio"):
                    audio_base64 = payload["audio"]
                elif payload.get("audio_url"):
                    audio_url = payload["audio_url"]

                return SynthesisResult(
                    text=speech_text,
                    audio_base64=audio_base64,
                    audio_url=audio_url,
                    mime_type="audio/wav",
                    provider=self.name,
                    latency_ms=round((time.perf_counter() - started) * 1000, 2),
                    meta={
                        "model": self.model,
                        "speaker": self.speaker,
                        "attempt": attempt,
                        "reused_client": True,
                        "clipped": speech_text != text.strip(),
                    },
                )
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning("sarvam_tts_attempt_failed attempt=%s error=%s", attempt, exc)

        raise RuntimeError(f"Sarvam TTS failed: {last_error}")
