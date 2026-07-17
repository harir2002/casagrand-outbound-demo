"""μ-law / PCM helpers for Twilio Media Streams (8 kHz) ↔ pipeline WAV/PCM."""

from __future__ import annotations

import audioop
import io
import struct
import wave

TWILIO_SAMPLE_RATE = 8000
TWILIO_CHANNELS = 1
TWILIO_SAMPLE_WIDTH = 2  # after μ-law decode → 16-bit PCM


def mulaw_to_pcm16(mulaw: bytes) -> bytes:
    """Decode G.711 μ-law bytes to 16-bit little-endian PCM."""
    if not mulaw:
        return b""
    return audioop.ulaw2lin(mulaw, TWILIO_SAMPLE_WIDTH)


def pcm16_to_mulaw(pcm: bytes) -> bytes:
    """Encode 16-bit little-endian PCM to G.711 μ-law."""
    if not pcm:
        return b""
    return audioop.lin2ulaw(pcm, TWILIO_SAMPLE_WIDTH)


def resample_pcm16(pcm: bytes, *, src_rate: int, dst_rate: int) -> bytes:
    """Resample mono 16-bit PCM between sample rates."""
    if not pcm or src_rate == dst_rate:
        return pcm
    converted, _ = audioop.ratecv(pcm, TWILIO_SAMPLE_WIDTH, TWILIO_CHANNELS, src_rate, dst_rate, None)
    return converted


def pcm16_to_wav_bytes(
    pcm: bytes,
    *,
    sample_rate: int = TWILIO_SAMPLE_RATE,
    channels: int = TWILIO_CHANNELS,
    sample_width: int = TWILIO_SAMPLE_WIDTH,
) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return buf.getvalue()


def wav_bytes_to_pcm16(wav_bytes: bytes) -> tuple[bytes, int]:
    """Return (pcm16, sample_rate) from a WAV blob."""
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        channels = wf.getnchannels()
        width = wf.getsampwidth()
        rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())
    if width != 2:
        frames = audioop.lin2lin(frames, width, 2)
    if channels > 1:
        frames = audioop.tomono(frames, 2, 0.5, 0.5)
    return frames, rate


def mulaw_frames_to_wav(mulaw: bytes, *, sample_rate: int = TWILIO_SAMPLE_RATE) -> bytes:
    """Twilio inbound μ-law → WAV suitable for Sarvam STT."""
    pcm = mulaw_to_pcm16(mulaw)
    return pcm16_to_wav_bytes(pcm, sample_rate=sample_rate)


def pcm_or_wav_to_mulaw(
    audio: bytes,
    *,
    src_sample_rate: int | None = None,
    is_wav: bool = False,
) -> bytes:
    """Convert pipeline PCM/WAV (often 22.05 kHz) to Twilio μ-law @ 8 kHz."""
    if is_wav or (len(audio) > 44 and audio[:4] == b"RIFF"):
        pcm, rate = wav_bytes_to_pcm16(audio)
    else:
        pcm = audio
        rate = src_sample_rate or TWILIO_SAMPLE_RATE
    if rate != TWILIO_SAMPLE_RATE:
        pcm = resample_pcm16(pcm, src_rate=rate, dst_rate=TWILIO_SAMPLE_RATE)
    return pcm16_to_mulaw(pcm)


def is_mostly_silence_mulaw(mulaw: bytes, *, threshold: int = 64) -> bool:
    """Heuristic: μ-law 0xFF is silence; treat near-silence frames as quiet."""
    if not mulaw:
        return True
    # Count bytes close to 0xFF (idle channel)
    quiet = sum(1 for b in mulaw if b >= 0xFF - 2 or b <= 2)
    return (quiet / len(mulaw)) >= 0.92 and _pcm_peak(mulaw_to_pcm16(mulaw)) < threshold


def _pcm_peak(pcm: bytes) -> int:
    if len(pcm) < 2:
        return 0
    peak = 0
    for i in range(0, len(pcm) - 1, 2):
        sample = abs(struct.unpack_from("<h", pcm, i)[0])
        if sample > peak:
            peak = sample
    return peak
