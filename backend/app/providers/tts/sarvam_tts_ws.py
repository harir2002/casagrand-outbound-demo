"""Sarvam TTS WebSocket streaming adapter.

Connects to Sarvam's TTS WS, streams PCM audio chunks, aggregates them into a
WAV payload for the existing CallView contract, and records first-audio timings.
The connect factory is injectable so CI can mock sockets without live network.
"""

from __future__ import annotations

import base64
import json
import time
import wave
from collections.abc import Awaitable, Callable
from io import BytesIO
from typing import Any
from urllib.parse import urlencode

from app.core.logging import get_logger
from app.models.session import Language
from app.providers.tts.base import TTSProvider
from app.providers.tts.sarvam_tts import _LANG_MAP, SarvamTTS
from app.providers.types import SynthesisResult

logger = get_logger(__name__)

ConnectFn = Callable[..., Awaitable[Any]]


def _default_connect(*args: Any, **kwargs: Any) -> Awaitable[Any]:
    import websockets

    return websockets.connect(*args, **kwargs)


def pcm_chunks_to_wav_base64(
    pcm: bytes,
    *,
    sample_rate: int = 22050,
    channels: int = 1,
    sample_width: int = 2,
) -> str:
    buf = BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return base64.b64encode(buf.getvalue()).decode("ascii")


class SarvamStreamingTTS(TTSProvider):
    """WebSocket-only Sarvam TTS. Prefer HybridSarvamTTS for production use."""

    name = "sarvam"

    def __init__(
        self,
        api_key: str,
        *,
        ws_url: str = "wss://api.sarvam.ai/text-to-speech/ws",
        model: str = "bulbul:v2",
        speaker: str = "anushka",
        sample_rate: int = 22050,
        timeout_seconds: float = 20.0,
        connect_fn: ConnectFn | None = None,
    ) -> None:
        self.api_key = api_key
        self.ws_url = ws_url.rstrip("/")
        self.model = model
        self.speaker = speaker
        self.sample_rate = sample_rate
        self.timeout_seconds = timeout_seconds
        self._connect: ConnectFn = connect_fn or _default_connect

    def _endpoint(self) -> str:
        query = urlencode({"model": self.model, "send_completion_event": "true"})
        return f"{self.ws_url}?{query}"

    async def synthesize(self, text: str, language: Language) -> SynthesisResult:
        if not text.strip():
            raise ValueError("text is empty")

        started = time.perf_counter()
        speech_text = SarvamTTS._clip_for_speech(text)
        pcm_parts: list[bytes] = []
        first_audio_ms: float | None = None
        stream_start_ms: float | None = None
        chunk_count = 0

        headers = {"api-subscription-key": self.api_key}
        endpoint = self._endpoint()

        async with awaitable_context(self._connect(endpoint, additional_headers=headers)) as ws:
            stream_start_ms = round((time.perf_counter() - started) * 1000, 2)
            config_message = {
                "type": "config",
                "data": {
                    "target_language_code": _LANG_MAP.get(language, "en-IN"),
                    "speaker": self.speaker,
                    "speech_sample_rate": str(self.sample_rate),
                    "enable_preprocessing": True,
                    "min_buffer_size": 50,
                    "max_chunk_length": 150,
                    "output_audio_codec": "linear16",
                    "pace": 1.0,
                    "model": self.model,
                },
            }
            await ws.send(json.dumps(config_message))
            await ws.send(json.dumps({"type": "text", "data": {"text": speech_text}}))
            await ws.send(json.dumps({"type": "flush"}))

            deadline = time.perf_counter() + self.timeout_seconds
            async for raw in ws:
                if time.perf_counter() > deadline:
                    raise TimeoutError("Sarvam TTS WebSocket timed out waiting for audio")
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8", errors="ignore")
                if not raw:
                    continue
                msg = json.loads(raw)
                msg_type = msg.get("type")
                data = msg.get("data") or {}

                if msg_type == "audio":
                    audio_b64 = data.get("audio")
                    if not audio_b64:
                        continue
                    if first_audio_ms is None:
                        first_audio_ms = round((time.perf_counter() - started) * 1000, 2)
                    pcm_parts.append(base64.b64decode(audio_b64))
                    chunk_count += 1
                elif msg_type == "event" and data.get("event_type") == "final":
                    break
                elif msg_type == "error":
                    raise RuntimeError(f"Sarvam TTS WS error: {data.get('message') or msg}")

        if not pcm_parts:
            raise RuntimeError("Sarvam TTS WebSocket returned no audio chunks")

        pcm = b"".join(pcm_parts)
        audio_base64 = pcm_chunks_to_wav_base64(pcm, sample_rate=self.sample_rate)
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        if first_audio_ms is None:
            first_audio_ms = latency_ms

        return SynthesisResult(
            text=speech_text,
            audio_base64=audio_base64,
            audio_url=None,
            mime_type="audio/wav",
            provider=self.name,
            latency_ms=latency_ms,
            meta={
                "model": self.model,
                "speaker": self.speaker,
                "transport": "websocket",
                "streaming": True,
                "fallback_used": False,
                "stream_start_ms": stream_start_ms,
                "first_audio_ms": first_audio_ms,
                "chunks": chunk_count,
                "sample_rate": self.sample_rate,
                "clipped": speech_text != text.strip(),
            },
        )


class awaitable_context:
    """Support both `async with connect(...)` and `async with await connect(...)`."""

    def __init__(self, value: Any) -> None:
        self._value = value
        self._cm: Any = None

    async def __aenter__(self) -> Any:
        value = self._value
        if hasattr(value, "__await__"):
            value = await value
        self._cm = value
        enter = getattr(value, "__aenter__", None)
        if enter is not None:
            return await enter()
        return value

    async def __aexit__(self, exc_type, exc, tb) -> bool | None:  # noqa: ANN001
        if self._cm is None:
            return None
        exit_fn = getattr(self._cm, "__aexit__", None)
        if exit_fn is not None:
            return await exit_fn(exc_type, exc, tb)
        close = getattr(self._cm, "close", None)
        if close is not None:
            result = close()
            if hasattr(result, "__await__"):
                await result
        return None
