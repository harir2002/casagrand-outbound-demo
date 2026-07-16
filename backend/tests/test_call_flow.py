"""Integration tests for the stable /session/* call contract."""


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_contract_fields_on_start(client):
    response = client.post(
        "/session/start",
        json={"project_id": "highcity", "language": "en"},
    )
    assert response.status_code == 200
    body = response.json()
    required = {
        "session_id",
        "call_id",
        "active_project",
        "active_bucket",
        "active_language",
        "transcript",
        "memory_slots",
        "last_intent",
        "faq_source",
        "summary",
        "needs_handoff",
        "handoff_reason",
        "latency_ms",
        "call_status",
    }
    assert required.issubset(body.keys())
    assert body["session_id"] == body["call_id"]
    assert body["active_project"] == "highcity"
    assert body["active_bucket"] == "introduction"
    assert body["active_language"] == "en"
    assert body["reply_text"]
    assert body["faq_source"]


def test_turn_includes_provider_audio_fields(client):
    start = client.post(
        "/session/start",
        json={"project_id": "highcity", "language": "en"},
    )
    session_id = start.json()["session_id"]
    turn = client.post(
        "/session/turn",
        json={"session_id": session_id, "text": "Tell me about pricing"},
    )
    assert turn.status_code == 200
    body = turn.json()
    assert body["reply_text"]
    assert body["tts_provider"] == "stub"
    assert body["llm_provider"] in {"stub", "skipped"}
    assert body["audio_base64"]
    assert body["latency_ms"] is not None
    assert "provider_meta" in body
    timings = body["provider_meta"].get("timings") or {}
    assert "stt_ms" in timings
    assert "domain_ms" in timings
    assert "llm_ms" in timings
    assert "tts_ms" in timings
    assert "parallel_wall_ms" in timings
    assert "total_ms" in timings


def test_full_flow_introduction_to_closing_summary(client):
    start = client.post(
        "/session/start",
        json={"project_id": "highcity", "language": "en"},
    )
    assert start.status_code == 200
    session_id = start.json()["session_id"]
    assert start.json()["active_bucket"] == "introduction"

    education = client.post(
        "/session/turn",
        json={"session_id": session_id, "text": "yes"},
    )
    assert education.status_code == 200
    assert education.json()["active_bucket"] == "education"
    assert len(education.json()["transcript"]) >= 3

    pricing = client.post(
        "/session/turn",
        json={"session_id": session_id, "text": "What is the pricing?"},
    )
    assert pricing.status_code == 200
    body = pricing.json()
    assert body["last_intent"] == "pricing"
    assert body["active_bucket"] == "education"
    assert body["faq_source"]
    assert "pricing" in (body["faq_source"] or "")

    visit = client.post(
        "/session/turn",
        json={
            "session_id": session_id,
            "text": "I want to book a site visit on saturday",
        },
    )
    assert visit.status_code == 200
    visit_body = visit.json()
    assert visit_body["active_bucket"] == "next_steps"
    assert visit_body["memory_slots"]["site_visit_interest"] is True
    assert visit_body["memory_slots"]["site_visit_preferred_day"] == "saturday"

    closing = client.post(
        "/session/turn",
        json={"session_id": session_id, "text": "yes, continue"},
    )
    assert closing.status_code == 200
    close_body = closing.json()
    assert close_body["active_bucket"] == "closing_summary"
    assert close_body["summary"]
    assert "Highcity" in close_body["summary"]
    assert close_body["call_status"] == "completed"

    state = client.get(f"/session/state?session_id={session_id}")
    assert state.status_code == 200
    assert state.json()["active_bucket"] == "closing_summary"
    assert state.json()["summary"]


def test_language_context_fallback_handoff_and_reset(client):
    start = client.post(
        "/session/start",
        json={"project_id": "highcity", "language": "en"},
    )
    session_id = start.json()["session_id"]

    lang = client.post(
        "/session/turn",
        json={"session_id": session_id, "text": "Switch to Tanglish"},
    )
    assert lang.json()["active_language"] == "tanglish"
    assert lang.json()["last_intent"] == "language_switch"

    switch = client.post(
        "/session/turn",
        json={"session_id": session_id, "text": "Tell me about Mercury"},
    )
    assert switch.json()["active_project"] == "mercury"
    assert switch.json()["last_intent"] == "context_switch"
    assert switch.json()["active_bucket"] == "education"

    ood = client.post(
        "/session/turn",
        json={"session_id": session_id, "text": "What is the weather in Mumbai?"},
    )
    assert ood.json()["last_intent"] == "out_of_domain"
    assert ood.json()["call_status"] == "fallback"
    assert "safe_fallback" in (ood.json()["faq_source"] or "")

    handoff = client.post(
        "/session/turn",
        json={
            "session_id": session_id,
            "text": "Please transfer me to a human advisor",
        },
    )
    assert handoff.json()["needs_handoff"] is True
    assert handoff.json()["call_status"] == "handoff"
    assert handoff.json()["handoff_reason"] == "caller_requested_human"
    assert handoff.json()["handoff_payload"] is not None

    reset = client.post(
        "/session/reset",
        json={"session_id": session_id},
    )
    assert reset.status_code == 200
    reset_body = reset.json()
    assert reset_body["active_project"] == "mercury"
    assert reset_body["active_language"] == "tanglish"
    assert reset_body["active_bucket"] == "introduction"
    assert reset_body["summary"] is None
    assert reset_body["needs_handoff"] is False
    assert len(reset_body["transcript"]) == 1
