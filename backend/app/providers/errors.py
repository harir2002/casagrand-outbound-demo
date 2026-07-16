"""Provider configuration errors and selection helpers."""

from __future__ import annotations


class ProviderConfigError(RuntimeError):
    """Raised when live mode is misconfigured (missing keys / invalid selection)."""


class ProviderRuntimeError(RuntimeError):
    """Raised when a configured live provider fails at runtime."""

    def __init__(self, provider: str, message: str) -> None:
        self.provider = provider
        super().__init__(f"{provider}: {message}")
