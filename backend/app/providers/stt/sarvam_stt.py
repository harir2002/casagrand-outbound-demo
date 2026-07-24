"""Sarvam STT adapter (REST; persistent HTTP client)."""

from __future__ import annotations

import time

import httpx

from app.core.logging import get_logger
from app.models.session import Language
from app.providers.http_client import create_async_client
from app.providers.stt.base import STTProvider
from app.providers.types import TranscriptResult

logger = get_logger(__name__)

_LANG_MAP = {
    Language.EN: "en-IN",
    Language.TA: "ta-IN",
    # Tamil-primary code-mix; English loanwords kept via mode=codemix
    Language.TANGLISH: "ta-IN",
}


def _stt_mode_for(language: Language | None, configured_mode: str) -> str:
    """Prefer codemix for Tamil-primary calls; keep English on plain transcribe."""
    mode = (configured_mode or "transcribe").strip().lower()
    if language in (Language.TA, Language.TANGLISH):
        return mode if mode in {"codemix", "transcribe", "verbatim", "translit"} else "codemix"
    if language == Language.EN and mode == "codemix":
        return "transcribe"
    return mode or "transcribe"


class SarvamSTT(STTProvider):
    name = "sarvam"

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.sarvam.ai",
        model: str = "saaras:v3",
        mode: str = "transcribe",
        timeout_seconds: float = 20.0,
        max_retries: int = 1,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.mode = mode
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

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: Language | None = None,
        *,
        mime_type: str = "audio/wav",
    ) -> TranscriptResult:
        if not audio_bytes:
            raise ValueError("audio_bytes is empty")

        started = time.perf_counter()
        headers = {"api-subscription-key": self.api_key}
        data = {
            "model": self.model,
            "mode": _stt_mode_for(language, self.mode),
        }
        if language is not None:
            data["language_code"] = _LANG_MAP.get(language, "ta-IN")
        elif self.mode.strip().lower() == "codemix":
            # Tamil-primary default when caller omits language
            data["language_code"] = "ta-IN"

        extension = "wav"
        if "mpeg" in mime_type or "mp3" in mime_type:
            extension = "mp3"
        files = {"file": (f"audio.{extension}", audio_bytes, mime_type)}

        last_error: Exception | None = None
        client = self._get_client()
        for attempt in range(self.max_retries + 1):
            try:
                response = await client.post(
                    f"{self.base_url}/speech-to-text",
                    headers=headers,
                    data=data,
                    files=files,
                )
                response.raise_for_status()
                payload = response.json()
                text = (
                    payload.get("transcript")
                    or payload.get("text")
                    or payload.get("translation")
                    or ""
                )
                return TranscriptResult(
                    text=str(text).strip(),
                    language=language,
                    confidence=float(payload.get("confidence") or 0.9),
                    provider=self.name,
                    latency_ms=round((time.perf_counter() - started) * 1000, 2),
                    meta={
                        "model": self.model,
                        "attempt": attempt,
                        "reused_client": True,
                        "raw_keys": list(payload.keys()),
                    },
                )
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning("sarvam_stt_attempt_failed attempt=%s error=%s", attempt, exc)

        raise RuntimeError(f"Sarvam STT failed: {last_error}")
