"""Domain RAG service — FAQ / brochure / comparison retrieval with timing."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.kb.bootstrap import get_kb_repository, get_rag_index
from app.kb.schema import RetrievalHit
from app.models.session import Intent, Language


@dataclass
class RagResult:
    answer: str | None
    source: str | None
    hits: list[RetrievalHit] = field(default_factory=list)
    latency_ms: float = 0.0
    mode: str = "faq"


class DomainRagService:
    def retrieve_faq(
        self,
        *,
        query: str,
        project_id: str,
        language: Language,
        intent: Intent | None = None,
        top_k: int = 3,
    ) -> RagResult:
        started = time.perf_counter()
        index = get_rag_index()
        hits = index.search_faq(
            query,
            project_id=project_id,
            language=language.value,
            intent=intent.value if intent else None,
            top_k=top_k,
        )
        # Prefer exact FAQ card when intent is known
        if intent is not None:
            repo = get_kb_repository()
            card = repo.get_faq(project_id, intent.value, language.value)
            if card is not None and card.answer.strip():
                latency_ms = round((time.perf_counter() - started) * 1000, 2)
                return RagResult(
                    answer=card.answer,
                    source=card.source or f"faq:{card.faq_id}",
                    hits=hits,
                    latency_ms=latency_ms,
                    mode="faq",
                )

        best = hits[0] if hits else None
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        return RagResult(
            answer=best.text if best else None,
            source=best.source if best else None,
            hits=hits,
            latency_ms=latency_ms,
            mode="faq",
        )

    def retrieve_brochure(
        self,
        *,
        project_id: str,
        language: Language,
    ) -> RagResult:
        started = time.perf_counter()
        hits = get_rag_index().search_brochure(
            project_id, language=language.value, top_k=2
        )
        best = hits[0] if hits else None
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        return RagResult(
            answer=best.text if best else None,
            source=best.source if best else None,
            hits=hits,
            latency_ms=latency_ms,
            mode="brochure",
        )

    def retrieve_comparison(
        self,
        *,
        query: str,
        language: Language,
        project_ids: list[str] | None = None,
    ) -> RagResult:
        started = time.perf_counter()
        repo = get_kb_repository()
        cards = repo.comparison_cards(project_ids)
        if not cards:
            cards = repo.list_projects()

        lines: list[str] = []
        if language == Language.TA:
            lines.append("திட்ட ஒப்பீடு (approved demo facts):")
        elif language == Language.TANGLISH:
            lines.append("Project comparison (approved demo facts):")
        else:
            lines.append("Project comparison (approved demo facts only):")

        for card in cards:
            lines.append(
                f"- {card.name}: {card.typology} @ {card.location}; "
                f"from {card.pricing_from}; status {card.status}."
            )
        if language == Language.EN:
            lines.append("Indicative demo pricing only; final quote after site discussion.")
        else:
            lines.append("Indicative demo pricing only.")

        hits = get_rag_index().search_comparison(query, top_k=3)
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        answer = " ".join(lines)
        return RagResult(
            answer=answer,
            source="rag:comparison",
            hits=hits,
            latency_ms=latency_ms,
            mode="comparison",
        )


domain_rag = DomainRagService()
