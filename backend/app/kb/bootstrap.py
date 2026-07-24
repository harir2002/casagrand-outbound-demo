"""Startup bootstrap for knowledge repository + RAG index."""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger
from app.kb.loader import load_knowledge_base
from app.kb.rag_index import RagIndex
from app.kb.repository import KnowledgeRepository
from app.kb.seed_builder import build_kb_documents

logger = get_logger(__name__)

_repository: KnowledgeRepository | None = None
_rag_index: RagIndex | None = None
_status: dict[str, Any] = {"ready": False}


def init_knowledge_base(settings=None) -> dict[str, Any]:
    """Load HF/local KB and build the RAG index. Safe to call multiple times."""
    global _repository, _rag_index, _status
    settings = settings or get_settings()

    projects, faqs, escalations, source = load_knowledge_base(
        settings.hf_dataset_id,
        split=settings.hf_dataset_split,
    )
    _repository = KnowledgeRepository(
        projects, faqs, escalations, source=source
    )

    persist = (settings.rag_persist_directory or "").strip() or None
    index = RagIndex(
        persist_directory=persist,
        force_rebuild=bool(settings.rag_force_rebuild),
    )
    docs = build_kb_documents(projects, faqs, escalations)
    build_info = index.build(docs)
    _rag_index = index

    _status = {
        "ready": True,
        "source": source,
        "projects": len(projects),
        "faqs": len(faqs),
        "escalations": len(escalations),
        **build_info,
    }
    logger.info(
        "knowledge_base_ready source=%s rag_backend=%s docs=%s persist=%s",
        source,
        build_info.get("backend"),
        build_info.get("document_count"),
        persist or "(ephemeral)",
    )
    return dict(_status)


def get_kb_repository() -> KnowledgeRepository:
    if _repository is None:
        init_knowledge_base()
    assert _repository is not None
    return _repository


def get_rag_index() -> RagIndex:
    if _rag_index is None:
        init_knowledge_base()
    assert _rag_index is not None
    return _rag_index


def knowledge_status() -> dict[str, Any]:
    return dict(_status)


def reset_knowledge_base() -> None:
    """Test helper — clear singletons."""
    global _repository, _rag_index, _status
    _repository = None
    _rag_index = None
    _status = {"ready": False}
