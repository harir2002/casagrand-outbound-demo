"""Normalized internal KB schema (HF dataset → domain objects)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


RecordType = Literal["project", "faq", "escalation", "comparison"]


class ProjectCard(BaseModel):
    project_id: str
    name: str
    city: str = ""
    location: str = ""
    status: str = ""
    typology: str = ""
    pricing_from: str = ""
    amenities: list[str] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    education: str = ""
    site_visit_note: str = ""
    brochure_note: str = ""
    language: str = "en"
    aliases: list[str] = Field(default_factory=list)


class FAQCard(BaseModel):
    faq_id: str
    project_id: str
    intent: str
    category: str
    language: str
    question: str
    answer: str
    source: str = ""


class EscalationRule(BaseModel):
    rule_id: str
    trigger: str
    action: str = "handoff"
    language: str = "en"
    message: str = ""
    reason: str = ""


class KBDocument(BaseModel):
    """Chunk indexed for RAG retrieval (approved KB only)."""

    doc_id: str
    record_type: RecordType
    project_id: str = ""
    intent: str = ""
    category: str = ""
    language: str = "en"
    title: str = ""
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalHit(BaseModel):
    doc_id: str
    text: str
    score: float
    project_id: str = ""
    intent: str = ""
    category: str = ""
    language: str = "en"
    record_type: str = "faq"
    title: str = ""
    source: str = ""
