"""Shared TTS audio helpers (WAV wrapping for browser / Twilio pipelines)."""

from __future__ import annotations

import base64
import wave
from io import BytesIO


def pcm_chunks_to_wav_base64(
    pcm: bytes,
    *,
    sample_rate: int = 22050,
    channels: int = 1,
    sample_width: int = 2,
) -> str:
    """Wrap linear16 PCM into a mono WAV and return base64."""
    buf = BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return base64.b64encode(buf.getvalue()).decode("ascii")
