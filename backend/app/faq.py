"""Domain-bound FAQ responses. Answers only from project knowledge."""

from __future__ import annotations

from app.models import Intent, Language
from app.projects import PROJECTS_VERSION, get_project

SAFE_FALLBACK = {
    Language.EN: (
        "I can help with Casagrand project details, pricing ranges, location, "
        "amenities, site visits, and callbacks. For anything else, I can "
        "connect you to a human advisor."
    ),
    Language.TA: (
        "நான் Casagrand திட்ட விவரங்கள், விலை வரம்பு, இடம், வசதிகள், "
        "தள வருகை மற்றும் கால்பேக் பற்றி உதவ முடியும். மற்ற கேள்விகளுக்கு "
        "மனித ஆலோசகருடன் இணைக்கலாம்."
    ),
    Language.TANGLISH: (
        "Naan Casagrand project details, pricing, location, amenities, "
        "site visit, callback la help panna mudiyum. Vera topic na "
        "human advisor connect panni tharen."
    ),
}

HANDOFF_REPLY = {
    Language.EN: (
        "Sure — I'll arrange a human handoff. A Casagrand advisor will "
        "continue from here. Please stay on the line."
    ),
    Language.TA: (
        "சரி — மனித ஆலோசகருக்கு இணைக்கிறேன். Casagrand ஆலோசகர் "
        "தொடர்ந்து உதவுவார். தயவுசெய்து காத்திருக்கவும்."
    ),
    Language.TANGLISH: (
        "Sure — human advisor ku connect panren. Casagrand advisor "
        "continue pannuvaanga. Please wait pannunga."
    ),
}


def _pick(language: Language, mapping: dict[Language, str]) -> str:
    return mapping.get(language, mapping[Language.EN])


def answer_faq(
    intent: Intent,
    project_id: str,
    language: Language,
) -> tuple[str, str | None]:
    """Return (reply_text, faq_source). faq_source is None for non-FAQ intents."""
    project = get_project(project_id)
    if project is None:
        return _pick(language, SAFE_FALLBACK), None

    source_base = f"projects@{PROJECTS_VERSION}:{project_id}"

    if intent == Intent.OUT_OF_DOMAIN:
        return _pick(language, SAFE_FALLBACK), f"{source_base}:safe_fallback"

    if intent == Intent.HUMAN_HANDOFF:
        return _pick(language, HANDOFF_REPLY), f"{source_base}:handoff"

    if intent == Intent.PROJECT_INFO:
        text = _project_info(project, language)
        return text, f"{source_base}:project_info"

    if intent == Intent.PRICING:
        text = _pricing(project, language)
        return text, f"{source_base}:pricing"

    if intent == Intent.LOCATION:
        text = _location(project, language)
        return text, f"{source_base}:location"

    if intent == Intent.AMENITIES:
        text = _amenities(project, language)
        return text, f"{source_base}:amenities"

    if intent == Intent.SITE_VISIT:
        text = _site_visit(project, language)
        return text, f"{source_base}:site_visit"

    if intent == Intent.CALLBACK:
        text = _callback(project, language)
        return text, f"{source_base}:callback"

    return _pick(language, SAFE_FALLBACK), f"{source_base}:safe_fallback"


def introduction_prompt(project_id: str, language: Language) -> tuple[str, str]:
    project = get_project(project_id) or get_project("highcity")
    assert project is not None
    name = project["name"]
    if language == Language.TA:
        text = (
            f"வணக்கம்! நான் Casagrand குரல் உதவியாளர். இன்று {name} "
            f"பற்றி பேசலாம் — வசதிகள், இடம், விலை மற்றும் தள வருகை. "
            f"எப்படி உதவட்டுமா?"
        )
    elif language == Language.TANGLISH:
        text = (
            f"Vanakkam! Naan Casagrand voice assistant. Indha call la "
            f"{name} pathi discuss pannalam — amenities, location, pricing, "
            f"site visit. Eppadi help panna?"
        )
    else:
        text = (
            f"Hello! I'm the Casagrand voice assistant. Today we can talk "
            f"about {name} — amenities, location, pricing, and booking a "
            f"site visit. How can I help?"
        )
    return text, f"projects@{PROJECTS_VERSION}:{project['id']}:introduction"


def education_prompt(project_id: str, language: Language) -> tuple[str, str]:
    project = get_project(project_id) or get_project("highcity")
    assert project is not None
    education = project["education"]
    if language == Language.TA:
        text = f"{education} மேலும் விவரம் வேண்டுமா — வசதிகள், விலை அல்லது இடம்?"
    elif language == Language.TANGLISH:
        text = f"{education} Innum details venuma — amenities, pricing, illa location?"
    else:
        text = f"{education} Would you like amenities, pricing, or location next?"
    return text, f"projects@{PROJECTS_VERSION}:{project['id']}:education"


def _project_info(project: dict, language: Language) -> str:
    if language == Language.TA:
        return (
            f"{project['name']} — {project['typology']} @ {project['location']}. "
            f"நிலை: {project['status']}. முக்கிய அம்சங்கள்: "
            f"{'; '.join(project['highlights'])}."
        )
    if language == Language.TANGLISH:
        return (
            f"{project['name']} — {project['typology']} @ {project['location']}. "
            f"Status: {project['status']}. Highlights: "
            f"{'; '.join(project['highlights'])}."
        )
    return (
        f"{project['name']} offers {project['typology']} at {project['location']}. "
        f"Status: {project['status']}. Highlights: "
        f"{'; '.join(project['highlights'])}."
    )


def _pricing(project: dict, language: Language) -> str:
    note = (
        "Indicative demo pricing only; final quote after site discussion."
    )
    if language == Language.TA:
        return f"{project['name']} விலை: {project['pricing_from']}. {note}"
    if language == Language.TANGLISH:
        return f"{project['name']} pricing: {project['pricing_from']}. {note}"
    return f"{project['name']} pricing starts at {project['pricing_from']}. {note}"


def _location(project: dict, language: Language) -> str:
    if language == Language.TA:
        return f"{project['name']} இடம்: {project['location']} ({project['city']})."
    if language == Language.TANGLISH:
        return f"{project['name']} location: {project['location']} ({project['city']})."
    return f"{project['name']} is located at {project['location']} ({project['city']})."


def _amenities(project: dict, language: Language) -> str:
    amenities = ", ".join(project["amenities"])
    if language == Language.TA:
        return f"{project['name']} வசதிகள்: {amenities}."
    if language == Language.TANGLISH:
        return f"{project['name']} amenities: {amenities}."
    return f"{project['name']} amenities include: {amenities}."


def _site_visit(project: dict, language: Language) -> str:
    base = project["site_visit_note"]
    if language == Language.TA:
        return f"{base} வசதியான நாள் சொல்லுங்கள்."
    if language == Language.TANGLISH:
        return f"{base} Convenient day sollunga."
    return f"{base} Which day works for you?"


def _callback(project: dict, language: Language) -> str:
    if language == Language.TA:
        return (
            f"{project['name']} குறித்து கால்பேக் ஏற்பாடு செய்கிறேன். "
            f"விருப்பமான நேரம் சொல்லுங்கள்."
        )
    if language == Language.TANGLISH:
        return (
            f"{project['name']} pathi callback arrange panren. "
            f"Preferred time sollunga."
        )
    return (
        f"I'll arrange a callback about {project['name']}. "
        f"What time works best?"
    )
