"""Tests for Sarvam TTS WebSocket streaming with mocked sockets (no live network)."""

from __future__ import annotations

import base64
import json

import pytest

from app.models.session import Language
from app.providers.tts.hybrid_sarvam_tts import HybridSarvamTTS
from app.providers.tts.sarvam_tts import SarvamTTS
from app.providers.tts.sarvam_tts_ws import SarvamStreamingTTS, pcm_chunks_to_wav_base64
from app.providers.types import SynthesisResult


class FakeWebSocket:
    """Minimal async websocket stand-in for CI."""

    def __init__(self, inbound: list[str]) -> None:
        self._inbound = list(inbound)
        self.sent: list[str] = []

    async def __aenter__(self) -> FakeWebSocket:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def send(self, data: str) -> None:
        self.sent.append(data)

    def __aiter__(self) -> FakeWebSocket:
        return self

    async def __anext__(self) -> str:
        if not self._inbound:
            raise StopAsyncIteration
        return self._inbound.pop(0)

    async def close(self) -> None:
        return None


def _audio_msg(pcm: bytes) -> str:
    return json.dumps(
        {"type": "audio", "data": {"audio": base64.b64encode(pcm).decode("ascii")}}
    )


def _final_msg() -> str:
    return json.dumps({"type": "event", "data": {"event_type": "final"}})


@pytest.mark.asyncio
async def test_streaming_tts_aggregates_chunks_and_timings() -> None:
    chunk_a = b"\x01\x00" * 64
    chunk_b = b"\x02\x00" * 64
    inbound = [_audio_msg(chunk_a), _audio_msg(chunk_b), _final_msg()]
    fake = FakeWebSocket(inbound)

    def connect_fn(*_args, **_kwargs):
        return fake

    tts = SarvamStreamingTTS(
        "test-key",
        connect_fn=connect_fn,
        timeout_seconds=5.0,
    )
    result = await tts.synthesize("Hello from Casagrand Highcity.", Language.EN)

    assert result.audio_base64
    assert result.mime_type == "audio/wav"
    assert result.meta["transport"] == "websocket"
    assert result.meta["streaming"] is True
    assert result.meta["fallback_used"] is False
    assert result.meta["chunks"] == 2
    assert result.meta["first_audio_ms"] is not None
    assert result.meta["stream_start_ms"] is not None
    assert result.meta["first_audio_ms"] >= result.meta["stream_start_ms"]

    # config + text + flush
    assert len(fake.sent) == 3
    assert json.loads(fake.sent[0])["type"] == "config"
    assert json.loads(fake.sent[1])["type"] == "text"
    assert json.loads(fake.sent[2])["type"] == "flush"

    expected = pcm_chunks_to_wav_base64(chunk_a + chunk_b, sample_rate=22050)
    assert result.audio_base64 == expected


@pytest.mark.asyncio
async def test_streaming_tts_raises_on_provider_error() -> None:
    inbound = [json.dumps({"type": "error", "data": {"message": "bad request"}})]
    fake = FakeWebSocket(inbound)

    tts = SarvamStreamingTTS("test-key", connect_fn=lambda *_a, **_k: fake)
    with pytest.raises(RuntimeError, match="bad request"):
        await tts.synthesize("Pricing details.", Language.EN)


@pytest.mark.asyncio
async def test_hybrid_falls_back_to_http_when_ws_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    http = SarvamTTS("test-key")

    async def fake_http_synthesize(text: str, language: Language) -> SynthesisResult:
        return SynthesisResult(
            text=text,
            audio_base64=base64.b64encode(b"HTTP_AUDIO").decode("ascii"),
            mime_type="audio/wav",
            provider="sarvam",
            latency_ms=12.0,
            meta={"transport": "http"},
        )

    monkeypatch.setattr(http, "synthesize", fake_http_synthesize)

    class BrokenStreaming(SarvamStreamingTTS):
        async def synthesize(self, text: str, language: Language) -> SynthesisResult:
            raise RuntimeError("ws down")

    hybrid = HybridSarvamTTS(
        http,
        BrokenStreaming("test-key", connect_fn=lambda *_a, **_k: FakeWebSocket([])),
        prefer_streaming=True,
    )
    result = await hybrid.synthesize("Amenities list.", Language.EN)
    assert result.audio_base64
    assert result.meta["fallback_used"] is True
    assert result.meta["transport"] == "http"
    assert result.meta["first_audio_ms"] == 12.0


@pytest.mark.asyncio
async def test_hybrid_http_only_backup_path(monkeypatch: pytest.MonkeyPatch) -> None:
    http = SarvamTTS("test-key")

    async def fake_http_synthesize(text: str, language: Language) -> SynthesisResult:
        return SynthesisResult(
            text=text,
            audio_base64=base64.b64encode(b"HTTP_ONLY").decode("ascii"),
            mime_type="audio/wav",
            provider="sarvam",
            latency_ms=9.0,
            meta={},
        )

    monkeypatch.setattr(http, "synthesize", fake_http_synthesize)
    hybrid = HybridSarvamTTS(http, None, prefer_streaming=False)
    result = await hybrid.synthesize("Hello", Language.EN)
    assert result.meta["streaming"] is False
    assert result.meta["fallback_used"] is False
    assert result.meta["transport"] == "http"
    assert result.meta["first_audio_ms"] == 9.0
