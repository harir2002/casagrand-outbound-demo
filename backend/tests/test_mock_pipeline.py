import base64

import pytest

from app.models.session import Language
from tests.doubles.providers import StubLLM, StubSTT, StubTTS


@pytest.mark.asyncio
async def test_stub_stt_default_and_text_payload():
    stt = StubSTT(default_text="hello casagrand")
    empty = await stt.transcribe(b"", Language.EN)
    assert empty.text == "hello casagrand"
    assert empty.provider == "stub"

    custom = await stt.transcribe(b"text:What is the pricing?", Language.TA)
    assert custom.text == "What is the pricing?"


@pytest.mark.asyncio
async def test_stub_tts_returns_audio_payload():
    tts = StubTTS()
    result = await tts.synthesize("Vanakkam", Language.TANGLISH)
    assert result.provider == "stub"
    assert result.audio_base64
    decoded = base64.b64decode(result.audio_base64)
    assert decoded.startswith(b"STUB_AUDIO:")


@pytest.mark.asyncio
async def test_stub_llm_extracts_grounded_answer():
    llm = StubLLM()
    result = await llm.complete(
        "intro\nGROUNDED_ANSWER:\nApproved Highcity answer",
        Language.EN,
        system_prompt="stay grounded",
    )
    assert result.text == "Approved Highcity answer"
