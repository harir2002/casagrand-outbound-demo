from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings
from app.models.session import HealthResponse
from app.providers.factory import validate_live_provider_config

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    problems = validate_live_provider_config(settings)
    ready = not problems
    return HealthResponse(
        status="ok" if ready else "degraded",
        version=__version__,
        env=settings.app_env,
        provider_mode="test" if settings.is_test_provider_mode else "live",
        providers_ready=ready,
        provider_errors=problems,
        stt_provider=settings.stt_provider,
        tts_provider=settings.tts_provider,
        llm_provider=settings.llm_provider,
        tts_voice_id=settings.sarvam_tts_speaker or "anushka",
        tts_voice_name=settings.sarvam_tts_model or "bulbul:v2",
    )
