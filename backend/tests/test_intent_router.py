from app.models.session import Intent
from app.services.intent_router import route_utterance


def test_routes_pricing():
    result = route_utterance("What is the pricing for this project?", "highcity")
    assert result.intent == Intent.PRICING


def test_routes_location_tamil():
    result = route_utterance("இடம் எங்க?", "highcity")
    assert result.intent == Intent.LOCATION


def test_routes_amenities():
    result = route_utterance("What amenities are available?", "highcity")
    assert result.intent == Intent.AMENITIES


def test_routes_site_visit_with_day():
    result = route_utterance("I want to book a site visit on saturday", "highcity")
    assert result.intent == Intent.SITE_VISIT
    assert result.extracted_slots.get("site_visit_preferred_day") == "saturday"


def test_routes_callback():
    result = route_utterance("Please call me back at 5 pm", "highcity")
    assert result.intent == Intent.CALLBACK


def test_routes_brochure():
    result = route_utterance("Please send me the brochure", "highcity")
    assert result.intent == Intent.BROCHURE


def test_routes_language_switch():
    result = route_utterance("Please switch to Tamil", "highcity")
    assert result.intent == Intent.LANGUAGE_SWITCH
    assert result.detected_language is not None
    assert result.detected_language.value == "ta"


def test_routes_context_switch():
    result = route_utterance("Tell me about Mercury project", "highcity")
    assert result.intent == Intent.CONTEXT_SWITCH
    assert result.target_project_id == "mercury"


def test_routes_out_of_domain():
    result = route_utterance("What is the cricket score today?", "highcity")
    assert result.intent == Intent.OUT_OF_DOMAIN


def test_routes_human_handoff():
    result = route_utterance("I want to speak to a human agent", "highcity")
    assert result.intent == Intent.HUMAN_HANDOFF
