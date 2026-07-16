import base64

import pytest

from app.models.call_view import TurnRequest
from app.models.session import CreateSessionRequest, Language
from app.providers.factory import ProviderBundle
from app.services import call_service
from app.services.conversation_orchestrator import ConversationOrchestrator
from tests.doubles.providers import StubLLM, StubSTT, StubTTS


@pytest.fixture
def orchestrator():
    bundle = ProviderBundle(
        stt=StubSTT(),
        tts=StubTTS(),
        llm=StubLLM(),
        stt_name="stub",
        tts_name="stub",
        llm_name="stub",
        mode="test",
    )
    return ConversationOrchestrator(bundle)


@pytest.mark.asyncio
async def test_orchestrator_preserves_session_across_turns(orchestrator):
    created = call_service.create_session(
        CreateSessionRequest(project_id="highcity", language=Language.EN)
    )
    session_id = created.session.session_id

    first = await orchestrator.handle_turn(
        TurnRequest(session_id=session_id, text="yes", skip_llm=False)
    )
    assert first.active_bucket.value == "education"
    assert first.session_id == session_id
    assert first.reply_text
    assert first.audio_base64
    assert first.tts_provider == "stub"
    assert first.provider_meta.get("timings", {}).get("total_ms") is not None
    assert first.provider_meta.get("timings", {}).get("parallel_wall_ms") is not None
    assert first.provider_meta.get("optimization") == "parallel_llm_tts_grounded_audio"

    second = await orchestrator.handle_turn(
        TurnRequest(
            session_id=session_id,
            text="I want to book a site visit on saturday",
            skip_llm=True,
        )
    )
    assert second.active_bucket.value == "next_steps"
    assert second.memory_slots.site_visit_preferred_day == "saturday"
    assert second.active_project == "highcity"


@pytest.mark.asyncio
async def test_orchestrator_accepts_simulated_audio(orchestrator):
    created = call_service.create_session(
        CreateSessionRequest(project_id="mercury", language=Language.EN)
    )
    session_id = created.session.session_id
    audio = base64.b64encode(b"text:What are the amenities?").decode("ascii")

    view = await orchestrator.handle_turn(
        TurnRequest(session_id=session_id, audio_base64=audio, skip_llm=True)
    )
    assert view.last_intent.value == "amenities"
    assert view.active_project == "mercury"
    assert view.faq_source
    assert view.audio_base64
