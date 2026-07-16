from app.faq import answer_faq, introduction_prompt
from app.models import Intent, Language
from app.projects import PROJECTS_VERSION, get_project


def test_project_info_is_domain_bound():
    text, source = answer_faq(Intent.PROJECT_INFO, "highcity", Language.EN)
    project = get_project("highcity")
    assert project["name"] in text
    assert source.startswith(f"projects@{PROJECTS_VERSION}:highcity")


def test_pricing_mentions_indicative():
    text, source = answer_faq(Intent.PRICING, "avenuepark", Language.EN)
    assert "Avenuepark" in text or "avenuepark" in text.lower()
    assert "pricing" in source


def test_amenities_lists_known_items():
    text, _ = answer_faq(Intent.AMENITIES, "mercury", Language.TANGLISH)
    assert "clubhouse" in text.lower() or "pool" in text.lower()


def test_out_of_domain_safe_fallback():
    text, source = answer_faq(Intent.OUT_OF_DOMAIN, "highcity", Language.EN)
    assert "site visits" in text.lower() or "callbacks" in text.lower()
    assert "safe_fallback" in source


def test_handoff_reply():
    text, source = answer_faq(Intent.HUMAN_HANDOFF, "highcity", Language.TA)
    assert "ஆலோசகர்" in text or "மனித" in text
    assert "handoff" in source


def test_introduction_prompt_branded():
    text, source = introduction_prompt("highcity", Language.EN)
    assert "Casagrand" in text
    assert "Highcity" in text
    assert "introduction" in source


def test_unknown_project_falls_back():
    text, source = answer_faq(Intent.PRICING, "does-not-exist", Language.EN)
    assert source is None
    assert "Casagrand" in text
