"""Heuristic intent router — swappable with LLM adapter later."""

from __future__ import annotations

import re

from app.data.projects import resolve_project_alias
from app.models.session import Intent, Language, RouteResult

LANGUAGE_HINTS: dict[Language, list[str]] = {
    Language.TA: ["தமிழ்", "tamil la", "tamil-le", "தமிழில", "tamil", "to tamil"],
    Language.EN: ["english", "engla", "ஆங்கிலம்", "to english"],
    Language.TANGLISH: ["tanglish", "tamil english", "mix la", "டாங்கிஷ்", "to tanglish"],
}

INTENT_PATTERNS: list[tuple[Intent, list[str]]] = [
    (
        Intent.HUMAN_HANDOFF,
        [
            r"\bhuman\b",
            r"\bagent\b",
            r"\badvisor\b",
            r"\btransfer\b",
            r"speak to (a )?person",
            r"மனிதர்",
            r"ஆலோசகர்",
            r"human ku connect",
            r"person ku connect",
        ],
    ),
    (
        Intent.LANGUAGE_SWITCH,
        [
            r"\btamil\b",
            r"\benglish\b",
            r"\btanglish\b",
            r"switch (to )?language",
            r"change language",
            r"தமிழ்",
            r"ஆங்கிலம்",
            r"மொழி",
        ],
    ),
    (
        Intent.CONTEXT_SWITCH,
        [
            r"\bswitch (to |project )?",
            r"about (highcity|avenuepark|mercury|avenue park|high city)",
            r"other project",
            r"வேற (project|திட்டம்)",
            r"change project",
        ],
    ),
    (
        Intent.SITE_VISIT,
        [
            r"site visit",
            r"\bvisit\b",
            r"book (a )?visit",
            r"தள வருகை",
            r"site visit book",
            r"visit book",
        ],
    ),
    (
        Intent.CALLBACK,
        [
            r"\bcallback\b",
            r"call me",
            r"call back",
            r"கால்பேக்",
            r"call panna",
            r"ring panna",
        ],
    ),
    (
        Intent.BROCHURE,
        [
            r"\bbrochure\b",
            r"\bpamphlet\b",
            r"\bleaflet\b",
            r"send (me )?(details|pdf)",
            r"brochure anuppu",
        ],
    ),
    (
        Intent.PRICING,
        [
            r"\bprice\b",
            r"\bpricing\b",
            r"\bcost\b",
            r"\bbudget\b",
            r"விலை",
            r"rate",
            r"how much",
            r"evaalo",
            r"evlo",
        ],
    ),
    (
        Intent.LOCATION,
        [
            r"\blocation\b",
            r"\bwhere\b",
            r"\baddress\b",
            r"area",
            r"இடம்",
            r"எங்க",
            r"enge",
        ],
    ),
    (
        Intent.AMENITIES,
        [
            r"\bamenit",
            r"\bfacilit",
            r"\bpool\b",
            r"\bgym\b",
            r"clubhouse",
            r"வசதி",
            r"amenities",
        ],
    ),
    (
        Intent.PROJECT_INFO,
        [
            r"\bproject\b",
            r"\btell me\b",
            r"\babout\b",
            r"details",
            r"overview",
            r"விவரம்",
            r"pathi",
            r"sollu",
        ],
    ),
    (
        Intent.GREETING,
        [
            r"^\s*(hi|hello|hey|vanakkam|வணக்கம்)\b",
            r"good (morning|afternoon|evening)",
        ],
    ),
    (
        Intent.AFFIRM,
        [
            r"^\s*(yes|yeah|yep|ok|okay|sure|ஆம்|சரி|aam|sari)\b",
            r"go ahead",
            r"continue",
            r"next",
            r"அடுத்த",
        ],
    ),
]

OUT_OF_DOMAIN_HINTS = [
    r"\bstock\b",
    r"\bcrypto\b",
    r"\bweather\b",
    r"\brecipe\b",
    r"\bcricket\b",
    r"\bmovie\b",
    r"political",
    r"election",
]


def detect_language_switch(text: str) -> Language | None:
    lowered = text.lower()
    ordered = (Language.TANGLISH, Language.TA, Language.EN)
    for language in ordered:
        if any(h.lower() in lowered for h in LANGUAGE_HINTS[language]):
            return language
    return None


def route_utterance(text: str, current_project_id: str) -> RouteResult:
    cleaned = text.strip()
    lowered = cleaned.lower()
    extracted: dict = {}

    target_project = resolve_project_alias(cleaned)
    if target_project and target_project != current_project_id:
        extracted["target_project_id"] = target_project

    lang_switch = detect_language_switch(cleaned)
    if lang_switch is not None and _looks_like_language_request(lowered):
        return RouteResult(
            intent=Intent.LANGUAGE_SWITCH,
            confidence=0.9,
            detected_language=lang_switch,
            target_project_id=target_project,
            extracted_slots={"language": lang_switch.value, **extracted},
        )

    for pattern in OUT_OF_DOMAIN_HINTS:
        if re.search(pattern, lowered):
            return RouteResult(
                intent=Intent.OUT_OF_DOMAIN,
                confidence=0.85,
                target_project_id=target_project,
                extracted_slots=extracted,
            )

    if target_project and target_project != current_project_id:
        if re.search(r"switch|change|about|pathi|விவரம்|வேற", lowered):
            return RouteResult(
                intent=Intent.CONTEXT_SWITCH,
                confidence=0.88,
                target_project_id=target_project,
                extracted_slots=extracted,
            )

    best_intent = Intent.UNKNOWN
    best_score = 0.0
    for intent, patterns in INTENT_PATTERNS:
        hits = sum(1 for p in patterns if re.search(p, lowered, re.IGNORECASE))
        if hits == 0:
            continue
        score = min(0.95, 0.55 + 0.15 * hits)
        if score > best_score:
            best_score = score
            best_intent = intent

    if best_intent == Intent.UNKNOWN and target_project:
        return RouteResult(
            intent=(
                Intent.CONTEXT_SWITCH
                if target_project != current_project_id
                else Intent.PROJECT_INFO
            ),
            confidence=0.7,
            target_project_id=target_project,
            extracted_slots=extracted,
        )

    if best_intent == Intent.UNKNOWN:
        return RouteResult(
            intent=Intent.OUT_OF_DOMAIN,
            confidence=0.5,
            target_project_id=target_project,
            extracted_slots=extracted,
        )

    day = _extract_day(lowered)
    if day:
        extracted["site_visit_preferred_day"] = day
    time_pref = _extract_time(lowered)
    if time_pref:
        extracted["preferred_callback_time"] = time_pref

    return RouteResult(
        intent=best_intent,
        confidence=best_score,
        detected_language=lang_switch,
        target_project_id=target_project,
        extracted_slots=extracted,
    )


def _looks_like_language_request(lowered: str) -> bool:
    markers = [
        "tamil",
        "english",
        "tanglish",
        "தமிழ்",
        "ஆங்கிலம்",
        "language",
        "மொழி",
        "switch",
        "speak",
        "pesu",
    ]
    return any(m in lowered for m in markers)


def _extract_day(text: str) -> str | None:
    days = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "tomorrow",
        "today",
    ]
    for day in days:
        if day in text:
            return day
    return None


def _extract_time(text: str) -> str | None:
    match = re.search(r"\b(\d{1,2}\s?(am|pm)|morning|afternoon|evening)\b", text)
    return match.group(0) if match else None
