"""Provider factory — real Sarvam/Groq for live demo; stubs only in test mode."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.providers.errors import ProviderConfigError
from app.providers.llm.base import LLMProvider
from app.providers.llm.groq_llm import GroqLLM
from app.providers.stt.base import STTProvider
from app.providers.stt.sarvam_stt import SarvamSTT
from app.providers.tts.base import TTSProvider
from app.providers.tts.hybrid_sarvam_tts import HybridSarvamTTS
from app.providers.tts.sarvam_tts import SarvamTTS
from app.providers.tts.sarvam_tts_ws import SarvamStreamingTTS

logger = get_logger(__name__)


@dataclass(frozen=True)
class ProviderBundle:
    stt: STTProvider
    tts: TTSProvider
    llm: LLMProvider
    stt_name: str
    tts_name: str
    llm_name: str
    mode: str


def _normalize(name: str) -> str:
    return (name or "").strip().lower()


def validate_live_provider_config(settings: Settings | None = None) -> list[str]:
    """Return list of config problems for live mode. Empty means OK."""
    settings = settings or get_settings()
    if settings.is_test_provider_mode:
        return []

    problems: list[str] = []
    stt = _normalize(settings.stt_provider) or "sarvam"
    tts = _normalize(settings.tts_provider) or "sarvam"
    llm = _normalize(settings.llm_provider) or "groq"

    if stt in {"stub", "mock"} or tts in {"stub", "mock"} or llm in {"stub", "mock"}:
        problems.append(
            "Live demo cannot use stub/mock providers. "
            "Set PROVIDER_MODE=test only for automated tests."
        )

    if stt in {"sarvam", "auto"} and not settings.has_sarvam_key:
        problems.append("SARVAM_API_KEY is required for Sarvam STT in live mode.")
    if tts in {"sarvam", "auto"} and not settings.has_sarvam_key:
        problems.append("SARVAM_API_KEY is required for Sarvam TTS in live mode.")
    if llm in {"groq", "auto"} and not settings.has_groq_key:
        problems.append("GROQ_API_KEY is required for Groq LLM in live mode.")

    if stt not in {"sarvam", "auto"}:
        problems.append(f"Unsupported STT provider for live mode: {stt}")
    if tts not in {"sarvam", "auto"}:
        problems.append(f"Unsupported TTS provider for live mode: {tts}")
    if llm not in {"groq", "auto"}:
        problems.append(f"Unsupported LLM provider for live mode: {llm}")

    return problems


def resolve_stt_name(settings: Settings) -> str:
    choice = _normalize(settings.stt_provider) or "sarvam"
    if settings.is_test_provider_mode and choice in {"stub", "mock", "auto"}:
        return "stub" if choice in {"stub", "mock", "auto"} else choice
    if choice in {"sarvam", "auto"}:
        if not settings.has_sarvam_key and not settings.is_test_provider_mode:
            raise ProviderConfigError("SARVAM_API_KEY is required for STT (Sarvam).")
        return "sarvam" if settings.has_sarvam_key else "stub"
    if choice in {"stub", "mock"}:
        if not settings.is_test_provider_mode:
            raise ProviderConfigError("STT stub/mock is only allowed in test provider mode.")
        return "stub"
    raise ProviderConfigError(f"Unsupported STT provider: {choice}")


def resolve_tts_name(settings: Settings) -> str:
    choice = _normalize(settings.tts_provider) or "sarvam"
    if settings.is_test_provider_mode and choice in {"stub", "mock", "auto"}:
        return "stub" if choice in {"stub", "mock", "auto"} else choice
    if choice in {"sarvam", "auto"}:
        if not settings.has_sarvam_key and not settings.is_test_provider_mode:
            raise ProviderConfigError("SARVAM_API_KEY is required for TTS (Sarvam).")
        return "sarvam" if settings.has_sarvam_key else "stub"
    if choice in {"stub", "mock"}:
        if not settings.is_test_provider_mode:
            raise ProviderConfigError("TTS stub/mock is only allowed in test provider mode.")
        return "stub"
    raise ProviderConfigError(f"Unsupported TTS provider: {choice}")


def resolve_llm_name(settings: Settings) -> str:
    choice = _normalize(settings.llm_provider) or "groq"
    if settings.is_test_provider_mode and choice in {"stub", "mock", "auto"}:
        return "stub" if choice in {"stub", "mock", "auto"} else choice
    if choice in {"groq", "auto"}:
        if not settings.has_groq_key and not settings.is_test_provider_mode:
            raise ProviderConfigError("GROQ_API_KEY is required for LLM (Groq).")
        return "groq" if settings.has_groq_key else "stub"
    if choice in {"stub", "mock"}:
        if not settings.is_test_provider_mode:
            raise ProviderConfigError("LLM stub/mock is only allowed in test provider mode.")
        return "stub"
    raise ProviderConfigError(f"Unsupported LLM provider: {choice}")


def _build_stub_stt() -> STTProvider:
    from tests.doubles.providers import StubSTT

    return StubSTT()


def _build_stub_tts() -> TTSProvider:
    from tests.doubles.providers import StubTTS

    return StubTTS()


def _build_stub_llm() -> LLMProvider:
    from tests.doubles.providers import StubLLM

    return StubLLM()


def build_stt(settings: Settings | None = None) -> STTProvider:
    settings = settings or get_settings()
    name = resolve_stt_name(settings)
    if name == "sarvam":
        return SarvamSTT(
            settings.sarvam_api_key,
            base_url=settings.sarvam_base_url,
            model=settings.sarvam_stt_model,
            mode=settings.sarvam_stt_mode,
            timeout_seconds=settings.provider_timeout_seconds,
            max_retries=settings.provider_max_retries,
        )
    return _build_stub_stt()


def build_tts(settings: Settings | None = None) -> TTSProvider:
    settings = settings or get_settings()
    name = resolve_tts_name(settings)
    if name == "sarvam":
        http = SarvamTTS(
            settings.sarvam_api_key,
            base_url=settings.sarvam_base_url,
            model=settings.sarvam_tts_model,
            speaker=settings.sarvam_tts_speaker,
            timeout_seconds=settings.provider_timeout_seconds,
            max_retries=settings.provider_max_retries,
        )
        if settings.sarvam_tts_streaming:
            streaming = SarvamStreamingTTS(
                settings.sarvam_api_key,
                ws_url=settings.sarvam_tts_ws_url,
                model=settings.sarvam_tts_model,
                speaker=settings.sarvam_tts_speaker,
                sample_rate=settings.sarvam_tts_sample_rate,
                timeout_seconds=settings.provider_timeout_seconds,
            )
            return HybridSarvamTTS(http, streaming, prefer_streaming=True)
        # Explicit backup: optimized non-streaming HTTP-only path
        return HybridSarvamTTS(http, None, prefer_streaming=False)
    return _build_stub_tts()


def build_llm(settings: Settings | None = None) -> LLMProvider:
    settings = settings or get_settings()
    name = resolve_llm_name(settings)
    if name == "groq":
        return GroqLLM(
            settings.groq_api_key,
            base_url=settings.groq_base_url,
            model=settings.groq_llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            timeout_seconds=settings.provider_timeout_seconds,
            max_retries=settings.provider_max_retries,
            streaming=settings.groq_streaming,
        )
    return _build_stub_llm()


def build_provider_bundle(settings: Settings | None = None) -> ProviderBundle:
    settings = settings or get_settings()
    problems = validate_live_provider_config(settings)
    if problems:
        message = " | ".join(problems)
        logger.error("provider_config_invalid: %s", message)
        raise ProviderConfigError(message)

    stt_name = resolve_stt_name(settings)
    tts_name = resolve_tts_name(settings)
    llm_name = resolve_llm_name(settings)
    mode = "test" if settings.is_test_provider_mode else "live"

    bundle = ProviderBundle(
        stt=build_stt(settings),
        tts=build_tts(settings),
        llm=build_llm(settings),
        stt_name=stt_name,
        tts_name=tts_name,
        llm_name=llm_name,
        mode=mode,
    )
    logger.info(
        "providers_selected mode=%s stt=%s tts=%s llm=%s",
        bundle.mode,
        bundle.stt_name,
        bundle.tts_name,
        bundle.llm_name,
    )
    return bundle
