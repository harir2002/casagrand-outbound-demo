"""Noise-gate / VAD helpers for Twilio μ-law frames."""

from __future__ import annotations

import math
import struct

from app.integrations.twilio.audio_codec import (
    is_mostly_silence_mulaw,
    is_utterance_speech_mulaw,
    pcm16_to_mulaw,
)


def _tone_mulaw(*, samples: int = 160, amplitude: int = 8000, freq_hz: float = 400.0) -> bytes:
    pcm = bytearray()
    for i in range(samples):
        value = int(amplitude * math.sin(2 * math.pi * freq_hz * i / 8000.0))
        pcm += struct.pack("<h", max(-32767, min(32767, value)))
    return pcm16_to_mulaw(bytes(pcm))


def _quiet_mulaw(samples: int = 160, amplitude: int = 80) -> bytes:
    """Low-level ambient-like noise that must NOT trip speech VAD."""
    pcm = bytearray()
    for i in range(samples):
        value = int(amplitude * math.sin(2 * math.pi * 120.0 * i / 8000.0))
        pcm += struct.pack("<h", value)
    return pcm16_to_mulaw(bytes(pcm))


def test_ambient_noise_counts_as_silence():
    assert is_mostly_silence_mulaw(b"\xff" * 160) is True
    assert is_mostly_silence_mulaw(_quiet_mulaw()) is True


def test_loud_speech_frame_is_not_silence():
    assert is_mostly_silence_mulaw(_tone_mulaw()) is False


def test_noise_buffer_rejected_before_stt():
    noise = _quiet_mulaw(4000)
    assert is_utterance_speech_mulaw(noise) is False


def test_speech_buffer_accepted_for_stt():
    speech = b"".join(_tone_mulaw() for _ in range(25))
    assert is_utterance_speech_mulaw(speech) is True
