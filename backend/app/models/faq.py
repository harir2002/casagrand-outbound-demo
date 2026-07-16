from pydantic import BaseModel, Field

from app.models.session import Intent, Language


class FaqAnswer(BaseModel):
    intent: Intent
    project_id: str
    language: Language
    text: str
    source: str


class FaqLookupResult(BaseModel):
    found: bool
    text: str
    source: str | None = None
    is_fallback: bool = False
    extras: dict = Field(default_factory=dict)
