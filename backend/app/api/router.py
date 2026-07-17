from fastapi import APIRouter

from app.api.routes import call, campaigns, health, leads, twilio


def build_api_router() -> APIRouter:
    api = APIRouter()
    api.include_router(health.router)
    api.include_router(call.router)
    api.include_router(leads.router)
    api.include_router(campaigns.router)
    api.include_router(twilio.router)
    return api
