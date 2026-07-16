"""Build CallView responses with provider/audio metadata."""

from __future__ import annotations

from app.models.call_view import CallViewResponse
from app.providers.types import SynthesisResult, TranscriptResult
from app.services.call_view import to_call_view
from app.models.session import SessionResponse


def build_provider_call_view(
    session_result: SessionResponse,
    *,
    transcript: TranscriptResult | None = None,
    synthesis: SynthesisResult | None = None,
    provider_meta: dict | None = None,
    warnings: list[str] | None = None,
    stt_latency_ms: float | None = None,
    llm_latency_ms: float | None = None,
    tts_latency_ms: float | None = None,
    total_latency_ms: float | None = None,
) -> CallViewResponse:
    view = to_call_view(session_result)
    warning_text = None
    if warnings:
        warning_text = " | ".join(warnings)

    view.warning = warning_text or view.warning
    view.stt_provider = transcript.provider if transcript else (provider_meta or {}).get("stt")
    view.tts_provider = synthesis.provider if synthesis else (provider_meta or {}).get("tts")
    view.llm_provider = (provider_meta or {}).get("llm")
    view.audio_base64 = synthesis.audio_base64 if synthesis else None
    view.audio_url = synthesis.audio_url if synthesis else None
    view.audio_mime_type = synthesis.mime_type if synthesis else None
    view.stt_latency_ms = stt_latency_ms
    view.llm_latency_ms = llm_latency_ms
    view.tts_latency_ms = tts_latency_ms
    if total_latency_ms is not None:
        view.latency_ms = total_latency_ms
    view.provider_meta = provider_meta or {}
    return view
