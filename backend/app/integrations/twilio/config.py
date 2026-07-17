"""Twilio-specific config validation (reads from app Settings)."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class TwilioConfig:
    enabled: bool
    account_sid: str
    auth_token: str
    from_number: str
    public_base_url: str
    media_stream_path: str
    voice_webhook_path: str
    status_callback_path: str
    validate_signatures: bool

    @property
    def voice_webhook_url(self) -> str:
        return _join_url(self.public_base_url, self.voice_webhook_path)

    @property
    def media_stream_wss_url(self) -> str:
        base = self.public_base_url.strip().rstrip("/")
        path = self.media_stream_path if self.media_stream_path.startswith("/") else f"/{self.media_stream_path}"
        if base.startswith("https://"):
            return "wss://" + base[len("https://") :] + path
        if base.startswith("http://"):
            return "ws://" + base[len("http://") :] + path
        if base.startswith("wss://") or base.startswith("ws://"):
            return base + path
        return f"wss://{base}{path}"

    @property
    def status_callback_url(self) -> str:
        return _join_url(self.public_base_url, self.status_callback_path)


def _join_url(base: str, path: str) -> str:
    root = base.strip().rstrip("/")
    suffix = path if path.startswith("/") else f"/{path}"
    if root.startswith("http://") or root.startswith("https://"):
        return root + suffix
    return f"https://{root}{suffix}"


def load_twilio_config(settings: Settings | None = None) -> TwilioConfig:
    s = settings or get_settings()
    return TwilioConfig(
        enabled=bool(s.twilio_enabled),
        account_sid=s.twilio_account_sid.strip(),
        auth_token=s.twilio_auth_token.strip(),
        from_number=s.twilio_from_number.strip(),
        public_base_url=s.twilio_public_base_url.strip().rstrip("/"),
        media_stream_path=s.twilio_media_stream_path.strip() or "/twilio/media-stream",
        voice_webhook_path=s.twilio_voice_webhook_path.strip() or "/twilio/voice-webhook",
        status_callback_path=s.twilio_status_callback_path.strip() or "/twilio/status-callback",
        validate_signatures=bool(s.twilio_validate_signatures),
    )


def validate_twilio_config(config: TwilioConfig | None = None) -> list[str]:
    """Return human-readable problems. Empty list means ready (or Twilio disabled)."""
    cfg = config or load_twilio_config()
    if not cfg.enabled:
        return []
    problems: list[str] = []
    if not cfg.account_sid:
        problems.append("TWILIO_ACCOUNT_SID is required when TWILIO_ENABLED=true")
    if not cfg.auth_token:
        problems.append("TWILIO_AUTH_TOKEN is required when TWILIO_ENABLED=true")
    if not cfg.from_number:
        problems.append("TWILIO_FROM_NUMBER is required when TWILIO_ENABLED=true")
    if not cfg.public_base_url:
        problems.append(
            "TWILIO_PUBLIC_BASE_URL is required when TWILIO_ENABLED=true "
            "(public https URL that Twilio can reach, e.g. ngrok)"
        )
    elif not (
        cfg.public_base_url.startswith("http://")
        or cfg.public_base_url.startswith("https://")
    ):
        problems.append("TWILIO_PUBLIC_BASE_URL must start with http:// or https://")
    return problems


def require_twilio_ready(settings: Settings | None = None) -> TwilioConfig:
    """Raise ValueError with a clear message when Twilio mode is on but misconfigured."""
    cfg = load_twilio_config(settings)
    problems = validate_twilio_config(cfg)
    if problems:
        raise ValueError("; ".join(problems))
    if not cfg.enabled:
        raise ValueError("Twilio is disabled. Set TWILIO_ENABLED=true to use telephony.")
    return cfg
