"""Streaming cascade / event-order tests (stub providers, no live sockets)."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.models.call_view import TurnRequest
from app.models.session import CreateSessionRequest, Language
from app.providers.factory import ProviderBundle
from app.services import call_service
from app.services.conversation_orchestrator import ConversationOrchestrator
from app.services.sentence_buffer import pop_complete_sentences
from tests.doubles.providers import StubLLM, StubSTT, StubTTS


def test_pop_complete_sentences_emits_on_terminator():
    ready, rest = pop_complete_sentences(
        "Casagrand Highcity pricing starts at demo rates. More details follow"
    )
    assert ready == ["Casagrand Highcity pricing starts at demo rates."]
    assert rest == "More details follow"


def test_pop_complete_sentences_early_emit_for_long_answer():
    """Long provisional text with trailing space should TTS before a period."""
    long_clause = (
        "Casagrand Highcity offers spacious two and three BHK homes with "
        "premium amenities across the community "
    )
    assert len(long_clause.strip()) >= 52
    ready, rest = pop_complete_sentences(long_clause)
    assert ready == [long_clause.strip()]
    assert rest == ""


def test_pop_complete_sentences_clause_break_for_long_answer():
    buffer = (
        "Pricing starts at indicative demo rates for two and three BHK homes, "
        "with flexible payment options still being finalized"
    )
    ready, rest = pop_complete_sentences(buffer)
    assert ready
    assert ready[0].startswith("Pricing starts")
    assert "flexible payment" in rest or rest.startswith("with flexible")


def test_pop_complete_sentences_keeps_short_faq_intact():
    """Short FAQ replies must not be split into tiny spoken fragments."""
    ready, rest = pop_complete_sentences("Yes, we do.")
    # Under min_chars / clause threshold — hold as remainder (flushed at stream end).
    assert ready == []
    assert "Yes" in rest

    ready2, rest2 = pop_complete_sentences(
        "Clubhouse and swimming pool are available on site. "
    )
    assert ready2 == ["Clubhouse and swimming pool are available on site."]
    assert rest2 == ""


def test_pop_complete_sentences_merges_short_opener():
    ready, rest = pop_complete_sentences(
        "Yes. We have a clubhouse and pool nearby. "
    )
    assert len(ready) == 1
    assert ready[0].startswith("Yes.")
    assert "clubhouse" in ready[0]
    assert rest == ""


@pytest.mark.asyncio
async def test_stub_llm_stream_text_chunks():
    llm = StubLLM()
    chunks = []
    async for delta in llm.stream_text(
        "ANSWER:\nPricing starts at demo rates.\nRewrite for speech only.",
        Language.EN,
    ):
        chunks.append(delta)
    assert chunks
    assert "".join(chunks).strip().startswith("Pricing")


@pytest.mark.asyncio
async def test_streaming_orchestrator_event_order():
    bundle = ProviderBundle(
        stt=StubSTT(),
        tts=StubTTS(),
        llm=StubLLM(),
        stt_name="stub",
        tts_name="stub",
        llm_name="stub",
        mode="test",
    )
    orch = ConversationOrchestrator(bundle)
    created = call_service.create_session(
        CreateSessionRequest(project_id="highcity", language=Language.EN)
    )
    events = []
    async for ev in orch.handle_turn_stream(
        TurnRequest(
            session_id=created.session.session_id,
            text="What is the pricing?",
            skip_llm=False,
        )
    ):
        events.append(ev)

    names = [e["event"] for e in events]
    assert names[0] == "stream_start"
    assert "audio_chunk" in names
    assert names[-1] == "stream_end"
    assert names.index("audio_chunk") < names.index("stream_end")

    end = events[-1]
    timings = end.get("timings") or {}
    assert timings.get("first_audio_ms") is not None
    assert timings.get("total_ms") is not None
    assert timings.get("stream_start_ms") is not None
    assert end.get("fallback_used") is False
    view = end.get("call_view") or {}
    assert view.get("audio_base64")
    assert view.get("provider_meta", {}).get("optimization") == "cascade_llm_stream_tts_stream"
    meta = view.get("provider_meta") or {}
    assert "timings" in meta
    assert meta.get("tts_fallback_used") is False


@pytest.mark.asyncio
async def test_streaming_audio_chunk_queue_ordering():
    """audio_chunk indices must be monotonic for sequential browser playback."""
    bundle = ProviderBundle(
        stt=StubSTT(),
        tts=StubTTS(),
        llm=StubLLM(),
        stt_name="stub",
        tts_name="stub",
        llm_name="stub",
        mode="test",
    )
    orch = ConversationOrchestrator(bundle)
    created = call_service.create_session(
        CreateSessionRequest(project_id="highcity", language=Language.EN)
    )
    events = []
    async for ev in orch.handle_turn_stream(
        TurnRequest(
            session_id=created.session.session_id,
            text="Tell me about amenities and pricing details please",
            skip_llm=False,
        )
    ):
        events.append(ev)

    chunks = [e for e in events if e.get("event") == "audio_chunk"]
    assert chunks, "expected at least one audio_chunk"
    indices = [c.get("index") for c in chunks]
    assert indices == sorted(indices)
    assert indices == list(range(len(indices)))
    for chunk in chunks:
        assert chunk.get("audio_base64")
        assert (chunk.get("mime_type") or "").startswith("audio/")
        assert isinstance(chunk["audio_base64"], str)
        assert len(chunk["audio_base64"]) > 0


@pytest.mark.asyncio
async def test_streaming_skip_llm_still_emits_audio():
    bundle = ProviderBundle(
        stt=StubSTT(),
        tts=StubTTS(),
        llm=StubLLM(),
        stt_name="stub",
        tts_name="stub",
        llm_name="stub",
        mode="test",
    )
    orch = ConversationOrchestrator(bundle)
    created = call_service.create_session(
        CreateSessionRequest(project_id="mercury", language=Language.EN)
    )
    events = []
    async for ev in orch.handle_turn_stream(
        TurnRequest(
            session_id=created.session.session_id,
            text="Tell me about amenities",
            skip_llm=True,
        )
    ):
        events.append(ev)
    assert events[0]["event"] == "stream_start"
    assert any(e["event"] == "audio_chunk" for e in events)
    assert events[-1]["event"] == "stream_end"
    end = events[-1]
    assert (end.get("timings") or {}).get("first_audio_ms") is not None
    assert "fallback_used" in end


def test_turn_stream_http_ndjson(client: TestClient):
    start = client.post(
        "/session/start", json={"project_id": "highcity", "language": "en"}
    )
    assert start.status_code == 200
    session_id = start.json()["session_id"]

    with client.stream(
        "POST",
        "/session/turn/stream",
        json={"session_id": session_id, "text": "What is the pricing?"},
    ) as response:
        assert response.status_code == 200
        lines = [ln for ln in response.iter_lines() if ln]
    assert lines
    events = [json.loads(ln) for ln in lines]
    assert events[0]["event"] == "stream_start"
    assert events[-1]["event"] == "stream_end"
    assert any(e["event"] == "audio_chunk" for e in events)
    chunks = [e for e in events if e["event"] == "audio_chunk"]
    indices = [c.get("index", i) for i, c in enumerate(chunks)]
    assert indices == sorted(indices)


def test_aggregated_turn_still_works(client: TestClient):
    start = client.post(
        "/session/start", json={"project_id": "highcity", "language": "en"}
    )
    session_id = start.json()["session_id"]
    turn = client.post(
        "/session/turn",
        json={"session_id": session_id, "text": "What is the pricing?"},
    )
    assert turn.status_code == 200
    body = turn.json()
    assert body.get("reply_text")
    assert body.get("audio_base64")
    assert body.get("provider_meta", {}).get("timings", {}).get("total_ms") is not None
    timings = body["provider_meta"]["timings"]
    assert timings.get("total_ms") is not None
