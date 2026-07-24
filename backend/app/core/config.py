from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "local"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    default_language: str = "ta"
    default_project: str = "highcity"

    # live = real providers required; test = stubs allowed for automated tests
    provider_mode: str = "live"
    allow_test_stubs: bool = False

    # Explicit names: sarvam (STT + TTS) | groq (LLM) | auto | stub
    stt_provider: str = "sarvam"
    tts_provider: str = "sarvam"
    llm_provider: str = "groq"

    # Sarvam STT + TTS (single API key)
    sarvam_api_key: str = ""
    sarvam_base_url: str = "https://api.sarvam.ai"
    sarvam_stt_model: str = "saaras:v3"
    # codemix keeps Tamil script dominant with English brand/product words
    sarvam_stt_mode: str = "codemix"
    sarvam_tts_model: str = "bulbul:v2"
    sarvam_tts_speaker: str = "anushka"
    sarvam_tts_streaming: bool = True
    sarvam_tts_ws_url: str = "wss://api.sarvam.ai/text-to-speech/ws"
    sarvam_tts_sample_rate: int = 22050
    tts_sample_rate: int = 22050

    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_llm_model: str = "llama-3.1-8b-instant"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 120
    # Stream tokens for earlier first-token timing (polish still non-binding for TTS)
    groq_streaming: bool = True

    provider_timeout_seconds: float = 20.0
    provider_max_retries: int = 1

    # Twilio telephony (optional; enabled via TWILIO_ENABLED=true)
    twilio_enabled: bool = False
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    twilio_public_base_url: str = ""
    twilio_media_stream_path: str = "/twilio/media-stream"
    twilio_voice_webhook_path: str = "/twilio/voice-webhook"
    twilio_validate_signatures: bool = True
    twilio_status_callback_path: str = "/twilio/status-callback"

    # Domain KB / RAG (HF dataset optional; local seed always available)
    hf_dataset_id: str = ""
    hf_dataset_split: str = "train"
    # Empty = ephemeral rebuild each startup (free Spaces).
    # Set to /data/casagrand_rag on Spaces with persistent storage.
    rag_persist_directory: str = ""
    rag_force_rebuild: bool = False
    rag_top_k: int = 3
    rag_enabled: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def has_sarvam_key(self) -> bool:
        return bool(self.sarvam_api_key.strip())

    @property
    def has_groq_key(self) -> bool:
        return bool(self.groq_api_key.strip())

    @property
    def is_test_provider_mode(self) -> bool:
        if self.provider_mode.strip().lower() == "test":
            return True
        return bool(self.allow_test_stubs)

    @property
    def has_twilio_credentials(self) -> bool:
        return bool(
            self.twilio_account_sid.strip()
            and self.twilio_auth_token.strip()
            and self.twilio_from_number.strip()
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
