def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_list_projects(client):
    response = client.get("/projects")
    assert response.status_code == 200
    ids = {p["id"] for p in response.json()}
    assert ids == {"highcity", "avenuepark", "mercury"}


def test_session_happy_path_flow(client):
    create = client.post(
        "/session",
        json={"project_id": "highcity", "language": "en"},
    )
    assert create.status_code == 200
    payload = create.json()
    session_id = payload["session"]["session_id"]
    assert payload["session"]["flow_bucket"] == "introduction"
    assert payload["reply"]["text"]

    education = client.post(
        f"/session/{session_id}/utterance",
        json={"text": "Tell me about this project"},
    )
    assert education.status_code == 200
    edu_body = education.json()
    assert edu_body["session"]["last_intent"] == "project_info"
    assert edu_body["session"]["flow_bucket"] == "education"
    assert edu_body["session"]["last_faq_source"]

    visit = client.post(
        f"/session/{session_id}/utterance",
        json={"text": "I want to book a site visit on saturday"},
    )
    assert visit.status_code == 200
    visit_body = visit.json()
    assert visit_body["session"]["flow_bucket"] == "next_steps"
    assert visit_body["session"]["memory"]["site_visit_interest"] is True
    assert visit_body["session"]["memory"]["site_visit_preferred_day"] == "saturday"

    summary = client.post(
        f"/session/{session_id}/utterance",
        json={"text": "yes, continue"},
    )
    assert summary.status_code == 200
    summary_body = summary.json()
    assert summary_body["session"]["flow_bucket"] == "summary"
    assert summary_body["session"]["final_summary"]
    assert "Highcity" in summary_body["session"]["final_summary"]


def test_language_and_context_switch(client):
    create = client.post("/session", json={"project_id": "highcity", "language": "en"})
    session_id = create.json()["session"]["session_id"]

    lang = client.post(
        f"/session/{session_id}/utterance",
        json={"text": "Switch to Tanglish"},
    )
    assert lang.status_code == 200
    assert lang.json()["session"]["language"] == "tanglish"

    switch = client.post(
        f"/session/{session_id}/utterance",
        json={"text": "Tell me about Mercury"},
    )
    assert switch.status_code == 200
    body = switch.json()
    assert body["session"]["project_id"] == "mercury"
    assert body["session"]["last_intent"] == "context_switch"


def test_out_of_domain_and_handoff(client):
    create = client.post("/session", json={"project_id": "avenuepark", "language": "en"})
    session_id = create.json()["session"]["session_id"]

    ood = client.post(
        f"/session/{session_id}/utterance",
        json={"text": "What is the weather in Mumbai?"},
    )
    assert ood.status_code == 200
    assert ood.json()["session"]["last_intent"] == "out_of_domain"
    assert "safe_fallback" in (ood.json()["session"]["last_faq_source"] or "")

    handoff = client.post(
        f"/session/{session_id}/utterance",
        json={"text": "Please transfer me to a human advisor"},
    )
    assert handoff.status_code == 200
    body = handoff.json()
    assert body["session"]["needs_handoff"] is True
    assert body["session"]["last_intent"] == "human_handoff"


def test_reset_session(client):
    create = client.post("/session", json={"project_id": "mercury", "language": "ta"})
    session_id = create.json()["session"]["session_id"]

    client.post(
        f"/session/{session_id}/utterance",
        json={"text": "விலை எவ்வளவு?"},
    )

    reset = client.post(f"/session/{session_id}/reset")
    assert reset.status_code == 200
    body = reset.json()
    assert body["session"]["project_id"] == "mercury"
    assert body["session"]["language"] == "ta"
    assert body["session"]["flow_bucket"] == "introduction"
    assert body["session"]["final_summary"] is None
    assert len(body["session"]["transcript"]) == 1
