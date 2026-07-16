"""Minimal runtime fallback — never silently swaps live providers for mocks."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.logging import get_logger
from app.models.session import Language
from app.providers.types import SynthesisResult

logger = get_logger(__name__)

FALLBACK_COPY = {
    Language.EN: (
        "I'm having trouble reaching our voice services right now. "
        "I can still help with approved project details in text, "
        "or I can connect you to a human advisor."
    ),
    Language.TA: (
        "தற்போது voice சேவை கிடைக்கவில்லை. அங்கீகரிக்கப்பட்ட திட்ட "
        "விவரங்களை உரையாக தருகிறேன், அல்லது மனித ஆலோசகருடன் இணைக்கலாம்."
    ),
    Language.TANGLISH: (
        "Ippa voice service issue irukku. Approved project details text la "
        "solluren, illa human advisor ku connect panni tharen."
    ),
}


@dataclass
class FallbackOutcome:
    reply_text: str
    warning: str
    needs_handoff: bool = False
    handoff_reason: str | None = None
    synthesis: SynthesisResult | None = None
    degraded: bool = True


def text_only_fallback(
    *,
    grounded_answer: str,
    language: Language,
    failed_provider: str,
    error: str,
) -> FallbackOutcome:
    """Keep domain answer (or clear notice); escalate handoff option when needed."""
    logger.warning(
        "provider_runtime_fallback provider=%s error=%s",
        failed_provider,
        error,
    )
    base = grounded_answer.strip() or FALLBACK_COPY.get(language, FALLBACK_COPY[Language.EN])
    notice = FALLBACK_COPY.get(language, FALLBACK_COPY[Language.EN])
    if grounded_answer.strip():
        reply = f"{base}\n\n({notice})"
        needs_handoff = False
        reason = None
    else:
        reply = notice
        needs_handoff = True
        reason = f"{failed_provider}_unavailable"

    return FallbackOutcome(
        reply_text=reply,
        warning=f"{failed_provider} unavailable: {error}",
        needs_handoff=needs_handoff,
        handoff_reason=reason,
        synthesis=None,
        degraded=True,
    )


def synthesis_placeholder(text: str, language: Language, failed_provider: str) -> SynthesisResult:
    """Return text-only synthesis metadata when TTS fails (no fake audio)."""
    return SynthesisResult(
        text=text,
        audio_base64=None,
        audio_url=None,
        mime_type="text/plain",
        provider=f"{failed_provider}-degraded",
        latency_ms=0.0,
        meta={"degraded": True, "reason": "tts_unavailable"},
    )
