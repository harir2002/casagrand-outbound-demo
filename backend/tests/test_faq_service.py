from app.data.projects import PROJECTS_VERSION
from app.models.session import Intent, Language
from app.services.faq_service import faq_service


def test_project_info_is_domain_bound():
    result = faq_service.lookup(Intent.PROJECT_INFO, "highcity", Language.EN)
    assert result.found is True
    assert "Highcity" in result.text
    assert result.source and result.source.startswith(f"projects@{PROJECTS_VERSION}:highcity")


def test_pricing_disclaimer_present():
    result = faq_service.lookup(Intent.PRICING, "avenuepark", Language.EN)
    assert "Avenuepark" in result.text
    assert "Indicative demo pricing" in result.text


def test_amenities_from_data_layer():
    result = faq_service.lookup(Intent.AMENITIES, "mercury", Language.TANGLISH)
    assert "clubhouse" in result.text.lower() or "pool" in result.text.lower()


def test_out_of_domain_safe_fallback():
    result = faq_service.lookup(Intent.OUT_OF_DOMAIN, "highcity", Language.EN)
    assert result.is_fallback is True
    assert "safe_fallback" in (result.source or "")


def test_unknown_project_falls_back():
    result = faq_service.lookup(Intent.PRICING, "does-not-exist", Language.EN)
    assert result.found is False
    assert result.is_fallback is True
    assert "Casagrand" in result.text


def test_introduction_asks_permission():
    result = faq_service.introduction("highcity", Language.EN)
    assert "Casagrand" in result.text
    assert "May I continue" in result.text or "continue" in result.text.lower()
