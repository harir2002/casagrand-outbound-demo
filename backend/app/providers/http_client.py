"""Shared httpx client helpers for provider adapters."""

from __future__ import annotations

import httpx


def create_async_client(timeout_seconds: float) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=httpx.Timeout(timeout_seconds, connect=5.0),
        limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
        http2=False,
    )
