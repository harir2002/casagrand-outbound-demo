"""Tests for HF/local KB load, RAG retrieval, and session memory."""

from __future__ import annotations

import pytest

from app.core.config import reset_settings_cache
from app.kb.bootstrap import (
    get_kb_repository,
    get_rag_index,
    init_knowledge_base,
    reset_knowledge_base,
)
from app.kb.seed_builder import build_kb_documents
from app.models.session import (
    CreateSessionRequest,
    Intent,
    Language,
    UtteranceRequest,
)
from app.services import call_service
from app.services.intent_router import route_utterance
from app.services.session_memory import to_session_memory
from app.services.session_store import store


@pytest.fixture(autouse=True)
def _fresh_kb(monkeypatch):
    monkeypatch.setenv("HF_DATASET_ID", "")
    monkeypatch.setenv("RAG_ENABLED", "true")
    monkeypatch.setenv("RAG_PERSIST_DIRECTORY", "")
    monkeypatch.setenv("RAG_FORCE_REBUILD", "true")
    reset_settings_cache()
    reset_knowledge_base()
    init_knowledge_base()
    store.clear()
    yield
    store.clear()
    reset_knowledge_base()
    reset_settings_cache()


def test_local_seed_loads_projects_and_faqs():
    repo = get_kb_repository()
    assert repo.source == "local_seed"
    assert repo.get_project("highcity") is not None
    assert repo.get_project("avenuepark") is not None
    assert repo.get_project("mercury") is not None
    pricing = repo.get_faq("highcity", "pricing", "en")
    assert pricing is not None
    assert "75" in pricing.answer or "pricing" in pricing.answer.lower()
    handoff = repo.get_escalation("human_handoff", "en")
    assert handoff is not None
    assert handoff.action == "handoff"


def test_rag_index_builds_and_retrieves_pricing():
    index = get_rag_index()
    assert index.document_count == len(build_kb_documents())
    hits = index.search_faq(
        "What is the pricing for Highcity?",
        project_id="highcity",
        language="en",
        intent="pricing",
        top_k=3,
    )
    assert hits
    assert hits[0].project_id == "highcity"
    assert "pricing" in hits[0].intent or "pricing" in hits[0].category


def test_rag_comparison_returns_all_projects():
    from app.services.domain_rag import domain_rag

    result = domain_rag.retrieve_comparison(
        query="compare Highcity and Mercury",
        language=Language.EN,
    )
    assert result.answer
    assert "Highcity" in result.answer
    assert "Mercury" in result.answer
    assert result.mode == "comparison"


def test_intent_router_detects_comparison():
    route = route_utterance("Can you compare Highcity vs Mercury?", "highcity")
    assert route.intent == Intent.COMPARISON


def test_session_memory_updates_after_turn():
    created = call_service.create_session(
        CreateSessionRequest(project_id="highcity", language=Language.EN)
    )
    sid = created.session.session_id
    result = call_service.process_utterance(
        sid,
        UtteranceRequest(text="I want a 2 BHK, budget around 70 lakh, call me at 5pm"),
    )
    memory = to_session_memory(result.session)
    assert memory.active_project == "highcity"
    assert memory.active_language == Language.EN
    assert memory.last_question
    assert memory.unit_preference == "2BHK"
    assert memory.callback_choice is not None or result.session.memory.preferred_callback_time


def test_handoff_updates_memory_summary():
    created = call_service.create_session(
        CreateSessionRequest(project_id="highcity", language=Language.EN)
    )
    sid = created.session.session_id
    result = call_service.process_utterance(
        sid,
        UtteranceRequest(text="Please transfer me to a human advisor"),
    )
    assert result.session.needs_handoff is True
    memory = to_session_memory(result.session)
    assert memory.needs_handoff is True
    assert memory.handoff_reason
    assert memory.summary or result.session.final_summary
    assert result.session.handoff_payload is not None


def test_comparison_turn_uses_rag_answer():
    created = call_service.create_session(
        CreateSessionRequest(project_id="highcity", language=Language.EN)
    )
    result = call_service.process_utterance(
        created.session.session_id,
        UtteranceRequest(text="Compare Highcity versus Avenuepark"),
    )
    assert result.reply is not None
    assert result.reply.intent == Intent.COMPARISON
    assert "Avenuepark" in result.reply.text or "Avenue" in result.reply.text
