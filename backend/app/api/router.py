from fastapi import APIRouter

from app.api.routes import call, health


def build_api_router() -> APIRouter:
    api = APIRouter()
    api.include_router(health.router)
    api.include_router(call.router)
    return api
