"""Approved FAQ answer templates — domain-bound only."""

from app.models.session import Intent, Language
from app.data.projects import PROJECTS_VERSION, get_project

SAFE_FALLBACK: dict[Language, str] = {
    Language.EN: (
        "I can help with Casagrand project details, pricing ranges, location, "
        "amenities, site visits, callbacks, and brochures. For anything else, "
        "I can connect you to a human advisor."
    ),
    Language.TA: (
        "நான் Casagrand திட்ட விவரங்கள், விலை வரம்பு, இடம், வசதிகள், "
        "தள வருகை, கால்பேக் மற்றும் brochure பற்றி உதவ முடியும். "
        "மற்ற கேள்விகளுக்கு மனித ஆலோசகருடன் இணைக்கலாம்."
    ),
    Language.TANGLISH: (
        "Naan Casagrand project details, pricing, location, amenities, "
        "site visit, callback, brochure la help panna mudiyum. Vera topic na "
        "human advisor connect panni tharen."
    ),
}

HANDOFF_REPLY: dict[Language, str] = {
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

PRICING_DISCLAIMER = (
    "Indicative demo pricing only; final quote after site discussion."
)


def source_key(project_id: str, topic: str) -> str:
    return f"projects@{PROJECTS_VERSION}:{project_id}:{topic}"


def build_introduction(project_id: str, language: Language) -> tuple[str, str]:
    project = get_project(project_id) or get_project("highcity")
    assert project is not None
    name = project.name
    if language == Language.TA:
        text = (
            f"வணக்கம்! நான் Casagrand குரல் உதவியாளர். இன்று {name} "
            f"பற்றி பேசலாம் — வசதிகள், இடம், விலை மற்றும் தள வருகை. "
            f"தொடர அனுமதி இருக்கிறதா?"
        )
    elif language == Language.TANGLISH:
        text = (
            f"Vanakkam! Naan Casagrand voice assistant. Indha call la "
            f"{name} pathi discuss pannalam — amenities, location, pricing, "
            f"site visit. Continue panna okay va?"
        )
    else:
        text = (
            f"Hello! I'm the Casagrand voice assistant. Today we can talk "
            f"about {name} — amenities, location, pricing, and booking a "
            f"site visit. May I continue?"
        )
    return text, source_key(project.id, "introduction")


def build_education(project_id: str, language: Language) -> tuple[str, str]:
    project = get_project(project_id) or get_project("highcity")
    assert project is not None
    education = project.education
    if language == Language.TA:
        text = f"{education} மேலும் விவரம் வேண்டுமா — வசதிகள், விலை அல்லது இடம்?"
    elif language == Language.TANGLISH:
        text = f"{education} Innum details venuma — amenities, pricing, illa location?"
    else:
        text = f"{education} Would you like amenities, pricing, or location next?"
    return text, source_key(project.id, "education")


def approved_answer_for(
    intent: Intent,
    project_id: str,
    language: Language,
) -> tuple[str, str] | None:
    """Return approved (text, source) or None if intent is not FAQ-backed."""
    project = get_project(project_id)
    if project is None:
        return None

    if intent == Intent.OUT_OF_DOMAIN:
        return SAFE_FALLBACK[language], source_key(project_id, "safe_fallback")

    if intent == Intent.HUMAN_HANDOFF:
        return HANDOFF_REPLY[language], source_key(project_id, "handoff")

    if intent == Intent.PROJECT_INFO:
        if language == Language.TA:
            text = (
                f"{project.name} — {project.typology} @ {project.location}. "
                f"நிலை: {project.status}. முக்கிய அம்சங்கள்: "
                f"{'; '.join(project.highlights)}."
            )
        elif language == Language.TANGLISH:
            text = (
                f"{project.name} — {project.typology} @ {project.location}. "
                f"Status: {project.status}. Highlights: "
                f"{'; '.join(project.highlights)}."
            )
        else:
            text = (
                f"{project.name} offers {project.typology} at {project.location}. "
                f"Status: {project.status}. Highlights: "
                f"{'; '.join(project.highlights)}."
            )
        return text, source_key(project_id, "project_info")

    if intent == Intent.PRICING:
        if language == Language.TA:
            text = f"{project.name} விலை: {project.pricing_from}. {PRICING_DISCLAIMER}"
        elif language == Language.TANGLISH:
            text = f"{project.name} pricing: {project.pricing_from}. {PRICING_DISCLAIMER}"
        else:
            text = (
                f"{project.name} pricing starts at {project.pricing_from}. "
                f"{PRICING_DISCLAIMER}"
            )
        return text, source_key(project_id, "pricing")

    if intent == Intent.LOCATION:
        if language == Language.TA:
            text = f"{project.name} இடம்: {project.location} ({project.city})."
        elif language == Language.TANGLISH:
            text = f"{project.name} location: {project.location} ({project.city})."
        else:
            text = (
                f"{project.name} is located at {project.location} ({project.city})."
            )
        return text, source_key(project_id, "location")

    if intent == Intent.AMENITIES:
        amenities = ", ".join(project.amenities)
        if language == Language.TA:
            text = f"{project.name} வசதிகள்: {amenities}."
        elif language == Language.TANGLISH:
            text = f"{project.name} amenities: {amenities}."
        else:
            text = f"{project.name} amenities include: {amenities}."
        return text, source_key(project_id, "amenities")

    if intent == Intent.SITE_VISIT:
        base = project.site_visit_note
        if language == Language.TA:
            text = f"{base} வசதியான நாள் சொல்லுங்கள்."
        elif language == Language.TANGLISH:
            text = f"{base} Convenient day sollunga."
        else:
            text = f"{base} Which day works for you?"
        return text, source_key(project_id, "site_visit")

    if intent == Intent.CALLBACK:
        if language == Language.TA:
            text = (
                f"{project.name} குறித்து கால்பேக் ஏற்பாடு செய்கிறேன். "
                f"விருப்பமான நேரம் சொல்லுங்கள்."
            )
        elif language == Language.TANGLISH:
            text = (
                f"{project.name} pathi callback arrange panren. "
                f"Preferred time sollunga."
            )
        else:
            text = (
                f"I'll arrange a callback about {project.name}. "
                f"What time works best?"
            )
        return text, source_key(project_id, "callback")

    if intent == Intent.BROCHURE:
        note = project.brochure_note
        if language == Language.TA:
            text = f"{note} உங்கள் விருப்பத்தை பதிவு செய்தேன்."
        elif language == Language.TANGLISH:
            text = f"{note} Request register paniren."
        else:
            text = f"{note} I've noted your request."
        return text, source_key(project_id, "brochure")

    return None
