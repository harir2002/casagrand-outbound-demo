"""FAQ service — returns only approved answers from the data layer."""

from __future__ import annotations

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

logger = get_logger(__name__)


class FaqService:
    def introduction(self, project_id: str, language: Language) -> FaqLookupResult:
        text, source = build_introduction(project_id, language)
        return FaqLookupResult(found=True, text=text, source=source)

    def education(self, project_id: str, language: Language) -> FaqLookupResult:
        text, source = build_education(project_id, language)
        return FaqLookupResult(found=True, text=text, source=source)

    def lookup(
        self,
        intent: Intent,
        project_id: str,
        language: Language,
    ) -> FaqLookupResult:
        if get_project(project_id) is None:
            logger.info("faq_fallback reason=unknown_project project_id=%s", project_id)
            return FaqLookupResult(
                found=False,
                text=SAFE_FALLBACK[language],
                source=None,
                is_fallback=True,
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


faq_service = FaqService()
