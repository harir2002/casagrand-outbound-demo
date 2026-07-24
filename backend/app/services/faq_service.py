"""FAQ service — RAG-backed lookup with approved template fallback."""

from __future__ import annotations

from app.core.config import get_settings
from app.core.logging import get_logger
from app.data.faq_data import (
    SAFE_FALLBACK,
    approved_answer_for,
    build_education,
    build_introduction,
    source_key,
)
from app.data.projects import get_project
from app.models.faq import FaqLookupResult
from app.models.session import Intent, Language
from app.services.domain_rag import RagResult, domain_rag

logger = get_logger(__name__)


class FaqService:
    def introduction(self, project_id: str, language: Language) -> FaqLookupResult:
        text, source = build_introduction(project_id, language)
        return FaqLookupResult(found=True, text=text, source=source)

    def education(self, project_id: str, language: Language) -> FaqLookupResult:
        # Keep approved education script text unchanged for the demo timeline.
        text, source = build_education(project_id, language)
        return FaqLookupResult(found=True, text=text, source=source)

    def lookup(
        self,
        intent: Intent,
        project_id: str,
        language: Language,
        *,
        query: str | None = None,
    ) -> FaqLookupResult:
        if get_project(project_id) is None:
            logger.info("faq_fallback reason=unknown_project project_id=%s", project_id)
            return FaqLookupResult(
                found=False,
                text=SAFE_FALLBACK[language],
                source=None,
                is_fallback=True,
            )

        settings = get_settings()
        rag_result: RagResult | None = None

        if settings.rag_enabled and intent == Intent.COMPARISON:
            rag_result = domain_rag.retrieve_comparison(
                query=query or "compare casagrand projects",
                language=language,
            )
            if rag_result.answer:
                return FaqLookupResult(
                    found=True,
                    text=rag_result.answer,
                    source=rag_result.source,
                    extras={"rag_ms": rag_result.latency_ms, "rag_mode": rag_result.mode},
                )

        if settings.rag_enabled and intent in {
            Intent.PROJECT_INFO,
            Intent.PRICING,
            Intent.LOCATION,
            Intent.AMENITIES,
            Intent.SITE_VISIT,
            Intent.CALLBACK,
            Intent.BROCHURE,
        }:
            rag_result = domain_rag.retrieve_faq(
                query=query or intent.value,
                project_id=project_id,
                language=language,
                intent=intent,
                top_k=settings.rag_top_k,
            )
            if rag_result.answer:
                return FaqLookupResult(
                    found=True,
                    text=rag_result.answer,
                    source=rag_result.source,
                    extras={"rag_ms": rag_result.latency_ms, "rag_mode": rag_result.mode},
                )

        approved = approved_answer_for(intent, project_id, language)
        if approved is None:
            logger.info(
                "faq_fallback reason=unsupported_intent intent=%s project_id=%s",
                intent.value,
                project_id,
            )
            return FaqLookupResult(
                found=False,
                text=SAFE_FALLBACK[language],
                source=source_key(project_id, "safe_fallback"),
                is_fallback=True,
            )

        text, source = approved
        is_fallback = intent == Intent.OUT_OF_DOMAIN
        if is_fallback:
            logger.info(
                "faq_fallback reason=out_of_domain project_id=%s",
                project_id,
            )
        return FaqLookupResult(
            found=not is_fallback,
            text=text,
            source=source,
            is_fallback=is_fallback,
        )

    def last_rag_meta(self) -> dict:
        return {}


faq_service = FaqService()
