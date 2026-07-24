"""RAG index over approved KB documents.

Uses Chroma when available (optional persistence under /data or local path).
Falls back to an in-memory cosine index with the same hashing embedder so
tests and free Spaces stay low-cost and deterministic.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.kb.embeddings import HashingEmbedder, cosine_similarity
from app.kb.schema import KBDocument, RetrievalHit

logger = get_logger(__name__)

COLLECTION_NAME = "casagrand_kb"


class RagIndex:
    def __init__(
        self,
        *,
        persist_directory: str | None = None,
        force_rebuild: bool = False,
        embedder: HashingEmbedder | None = None,
    ) -> None:
        self.persist_directory = persist_directory
        self.force_rebuild = force_rebuild
        self.embedder = embedder or HashingEmbedder()
        self.backend = "memory"
        self._docs: list[KBDocument] = []
        self._vectors: list[list[float]] = []
        self._chroma_collection = None
        self.document_count = 0

    def build(self, documents: list[KBDocument]) -> dict[str, Any]:
        started = time.perf_counter()
        self._docs = list(documents)
        self.document_count = len(documents)

        if self._try_build_chroma(documents):
            self.backend = "chroma"
        else:
            self.backend = "memory"
            self._vectors = [
                self.embedder.embed(self._index_text(doc)) for doc in documents
            ]

        build_ms = round((time.perf_counter() - started) * 1000, 2)
        logger.info(
            "rag_index_built backend=%s docs=%s persist=%s build_ms=%s",
            self.backend,
            self.document_count,
            self.persist_directory or "(ephemeral)",
            build_ms,
        )
        return {
            "backend": self.backend,
            "document_count": self.document_count,
            "persist_directory": self.persist_directory,
            "build_ms": build_ms,
        }

    def query(
        self,
        text: str,
        *,
        top_k: int = 3,
        project_id: str | None = None,
        intent: str | None = None,
        language: str | None = None,
        category: str | None = None,
        record_types: list[str] | None = None,
    ) -> list[RetrievalHit]:
        if not text.strip() or not self._docs:
            return []

        # Prefer Chroma when built; always apply metadata filters in Python for
        # consistent behavior across backends.
        query_vec = self.embedder.embed(
            self._query_text(
                text,
                project_id=project_id,
                intent=intent,
                language=language,
                category=category,
            )
        )
        scored: list[tuple[float, KBDocument]] = []
        for doc, vec in zip(self._docs, self._vectors or [None] * len(self._docs)):
            if project_id and doc.project_id and doc.project_id.lower() != project_id.lower():
                if doc.record_type != "escalation":
                    continue
            if language and doc.language and doc.record_type == "faq":
                if doc.language.lower() != language.lower():
                    continue
            if intent and doc.intent and doc.record_type == "faq":
                if doc.intent.lower() != intent.lower() and intent.lower() not in {
                    "brochure_summary",
                    "comparison",
                }:
                    # Soft boost path: still allow near-category matches via score
                    if doc.category.lower() != intent.lower():
                        continue
            if category and doc.category and doc.category.lower() != category.lower():
                continue
            if record_types and doc.record_type not in record_types:
                continue

            if vec is None:
                vec = self.embedder.embed(self._index_text(doc))
            score = cosine_similarity(query_vec, vec)
            scored.append((score, doc))

        scored.sort(key=lambda item: item[0], reverse=True)
        hits: list[RetrievalHit] = []
        for score, doc in scored[: max(1, top_k)]:
            answer = str(doc.metadata.get("answer") or doc.text)
            hits.append(
                RetrievalHit(
                    doc_id=doc.doc_id,
                    text=answer,
                    score=round(float(score), 4),
                    project_id=doc.project_id,
                    intent=doc.intent,
                    category=doc.category,
                    language=doc.language,
                    record_type=doc.record_type,
                    title=doc.title,
                    source=str(doc.metadata.get("source") or doc.doc_id),
                )
            )
        return hits

    def search_faq(
        self,
        query: str,
        *,
        project_id: str,
        language: str,
        intent: str | None = None,
        top_k: int = 3,
    ) -> list[RetrievalHit]:
        return self.query(
            query,
            top_k=top_k,
            project_id=project_id,
            language=language,
            intent=intent,
            record_types=["faq", "project"],
        )

    def search_brochure(
        self,
        project_id: str,
        *,
        language: str = "en",
        top_k: int = 2,
    ) -> list[RetrievalHit]:
        return self.query(
            f"brochure summary overview {project_id}",
            top_k=top_k,
            project_id=project_id,
            language=language,
            category="brochure",
            record_types=["project", "faq"],
        )

    def search_comparison(
        self,
        query: str,
        *,
        top_k: int = 3,
    ) -> list[RetrievalHit]:
        return self.query(
            query,
            top_k=top_k,
            record_types=["comparison", "project"],
            intent="comparison",
        )

    def _try_build_chroma(self, documents: list[KBDocument]) -> bool:
        try:
            import chromadb
            from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
        except ImportError:
            logger.info("rag_chroma_unavailable; using in-memory index")
            return False

        class _HashEF(EmbeddingFunction[Documents]):
            def __init__(self, embedder: HashingEmbedder) -> None:
                self._embedder = embedder

            def __call__(self, input: Documents) -> Embeddings:
                return self._embedder.embed_many(list(input))

        try:
            if self.persist_directory:
                path = Path(self.persist_directory)
                path.mkdir(parents=True, exist_ok=True)
                client = chromadb.PersistentClient(path=str(path))
            else:
                client = chromadb.Client()

            ef = _HashEF(self.embedder)
            existing = {c.name for c in client.list_collections()}
            if COLLECTION_NAME in existing and self.force_rebuild:
                client.delete_collection(COLLECTION_NAME)

            collection = client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=ef,
                metadata={"hnsw:space": "cosine"},
            )

            # Rebuild when empty or forced
            if self.force_rebuild or collection.count() == 0:
                if collection.count() > 0:
                    client.delete_collection(COLLECTION_NAME)
                    collection = client.get_or_create_collection(
                        name=COLLECTION_NAME,
                        embedding_function=ef,
                        metadata={"hnsw:space": "cosine"},
                    )
                if documents:
                    collection.add(
                        ids=[d.doc_id for d in documents],
                        documents=[self._index_text(d) for d in documents],
                        metadatas=[
                            {
                                "project_id": d.project_id,
                                "intent": d.intent,
                                "category": d.category,
                                "language": d.language,
                                "record_type": d.record_type,
                                "title": d.title[:200],
                                "source": str(d.metadata.get("source") or d.doc_id),
                            }
                            for d in documents
                        ],
                    )

            self._chroma_collection = collection
            # Keep memory vectors for filtered scoring (demo-scale corpus).
            self._vectors = [
                self.embedder.embed(self._index_text(doc)) for doc in documents
            ]
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("rag_chroma_build_failed error=%s; using memory", exc)
            self._chroma_collection = None
            return False

    @staticmethod
    def _index_text(doc: KBDocument) -> str:
        return " ".join(
            part
            for part in (
                doc.project_id,
                doc.intent,
                doc.category,
                doc.language,
                doc.title,
                doc.text,
            )
            if part
        )

    @staticmethod
    def _query_text(
        text: str,
        *,
        project_id: str | None,
        intent: str | None,
        language: str | None,
        category: str | None,
    ) -> str:
        parts = [text]
        if project_id:
            parts.append(project_id)
        if intent:
            parts.append(intent)
        if language:
            parts.append(language)
        if category:
            parts.append(category)
        return " ".join(parts)
