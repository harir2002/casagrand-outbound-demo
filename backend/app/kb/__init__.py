"""Domain knowledge base: HF dataset load, repository, and RAG index."""

from app.kb.bootstrap import get_kb_repository, get_rag_index, init_knowledge_base
from app.kb.schema import EscalationRule, FAQCard, ProjectCard

__all__ = [
    "EscalationRule",
    "FAQCard",
    "ProjectCard",
    "get_kb_repository",
    "get_rag_index",
    "init_knowledge_base",
]
