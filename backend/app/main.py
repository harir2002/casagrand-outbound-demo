from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.router import build_api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.providers.factory import validate_live_provider_config


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    logger = get_logger(__name__)

    problems = validate_live_provider_config(settings)
    if problems:
        for problem in problems:
            logger.error("PROVIDER CONFIG ERROR: %s", problem)
        logger.error(
            "Live demo providers are not ready. Set SARVAM_API_KEY and GROQ_API_KEY "
            "in backend/.env (or PROVIDER_MODE=test for automated tests only)."
        )
    else:
        logger.info(
            "providers_ready mode=%s stt=%s tts=%s llm=%s",
            "test" if settings.is_test_provider_mode else "live",
            settings.stt_provider,
            settings.tts_provider,
            settings.llm_provider,
        )

    app = FastAPI(
        title="Casagrand Voice Agent API",
        version=__version__,
        description="Local-first multilingual voice-agent demo backend",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "type": type(exc).__name__},
        )

    app.include_router(build_api_router())
    return app


app = create_app()
