import base64

import pytest

from app.models.call_view import TurnRequest
from app.models.session import CreateSessionRequest, Language
from app.providers.factory import ProviderBundle
from app.services import call_service
from app.services.audio_pipeline import AudioPipeline
from app.services.conversation_orchestrator import ConversationOrchestrator
from app.services.fallback_service import text_only_fallback
from tests.doubles.providers import (
    FailingLLM,
    FailingSTT,
    FailingTTS,
    StubLLM,
    StubSTT,
    StubTTS,
)


@pytest.mark.asyncio
async def test_tts_failure_degrades_without_fake_audio():
    bundle = ProviderBundle(
        stt=StubSTT(),
        tts=FailingTTS(),
        llm=StubLLM(),
        stt_name="stub",
        tts_name="failing-tts",
        llm_name="stub",
        mode="test",
    )
    pipeline = AudioPipeline(bundle)
    outcome = await pipeline.synthesize("Approved answer", Language.EN)
    assert outcome.degraded is True
    assert outcome.warning
    assert outcome.synthesis.audio_base64 is None
    assert "tts" in (outcome.warning or "")


@pytest.mark.asyncio
async def test_stt_failure_raises_runtime_error():
    from app.providers.errors import ProviderRuntimeError

    bundle = ProviderBundle(
        stt=FailingSTT(),
        tts=StubTTS(),
        llm=StubLLM(),
        stt_name="failing-stt",
        tts_name="stub",
        llm_name="stub",
        mode="test",
    )
    pipeline = AudioPipeline(bundle)
    audio = base64.b64encode(b"text:hello").decode("ascii")
    with pytest.raises(ProviderRuntimeError):
        await pipeline.maybe_transcribe(
            text=None,
            audio_base64=audio,
            language=Language.EN,
        )


@pytest.mark.asyncio
async def test_orchestrator_llm_failure_keeps_grounded_answer():
    bundle = ProviderBundle(
        stt=StubSTT(),
        tts=StubTTS(),
        llm=FailingLLM(),
        stt_name="stub",
        tts_name="stub",
        llm_name="failing-llm",
        mode="test",
    )
    orchestrator = ConversationOrchestrator(bundle)
    created = call_service.create_session(
        CreateSessionRequest(project_id="highcity", language=Language.EN)
    )
    view = await orchestrator.handle_turn(
        TurnRequest(
            session_id=created.session.session_id,
            text="What is the pricing?",
            skip_llm=False,
        )
    )
    assert view.reply_text
    assert "pricing" in (view.faq_source or "")
    assert view.warning
    assert "llm" in (view.warning or "").lower()


def test_text_only_fallback_message():
    fb = text_only_fallback(
        grounded_answer="Highcity pricing details.",
        language=Language.EN,
        failed_provider="tts",
        error="timeout",
    )
    assert "Highcity pricing details." in fb.reply_text
    assert fb.degraded is True
    assert "tts" in fb.warning
