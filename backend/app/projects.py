"""Versioned Casagrand project knowledge (demo data, domain-bound)."""

from typing import Any

PROJECTS_VERSION = "2026.07.15"

PROJECTS: dict[str, dict[str, Any]] = {
    "highcity": {
        "id": "highcity",
        "name": "Casagrand Highcity",
        "city": "Chennai",
        "location": "Perumbakkam, Chennai",
        "status": "ready_to_move / under construction (demo)",
        "typology": "2 & 3 BHK apartments",
        "pricing_from": "INR 75 Lakh onwards (indicative demo)",
        "amenities": [
            "clubhouse",
            "swimming pool",
            "gym",
            "children's play area",
            "landscaped gardens",
            "24x7 security",
        ],
        "highlights": [
            "Well-connected residential location in South Chennai",
            "Designed for family living with community amenities",
            "Site visits available by appointment",
        ],
        "education": (
            "Casagrand Highcity in Perumbakkam offers 2 & 3 BHK homes with "
            "clubhouse, pool, gym, and landscaped open spaces. It is suited for "
            "buyers looking at South Chennai connectivity and community living."
        ),
        "site_visit_note": (
            "We can book a guided site visit for Highcity. A relationship "
            "manager will confirm slot and meeting point."
        ),
    },
    "avenuepark": {
        "id": "avenuepark",
        "name": "Casagrand Avenuepark",
        "city": "Chennai",
        "location": "Tambaram / South Chennai corridor (demo)",
        "status": "upcoming / booking open (demo)",
        "typology": "2 & 3 BHK apartments",
        "pricing_from": "INR 65 Lakh onwards (indicative demo)",
        "amenities": [
            "clubhouse",
            "jogging track",
            "indoor games",
            "multipurpose hall",
            "CCTV surveillance",
        ],
        "highlights": [
            "Focused on value and practical layouts",
            "Access to key southern transit nodes",
            "Amenities planned for everyday family use",
        ],
        "education": (
            "Casagrand Avenuepark is positioned for buyers seeking balanced "
            "pricing with essential lifestyle amenities in South Chennai. "
            "Layouts focus on usable space and community facilities."
        ),
        "site_visit_note": (
            "Avenuepark site visits can be scheduled. We will share access "
            "instructions and a preferred visit window."
        ),
    },
    "mercury": {
        "id": "mercury",
        "name": "Casagrand Mercury",
        "city": "Chennai",
        "location": "OMR / IT corridor adjacency (demo)",
        "status": "launch / early booking (demo)",
        "typology": "premium 2 & 3 BHK apartments",
        "pricing_from": "INR 90 Lakh onwards (indicative demo)",
        "amenities": [
            "premium clubhouse",
            "infinity / leisure pool",
            "work-from-home lounge",
            "sky deck",
            "concierge desk (demo)",
        ],
        "highlights": [
            "Designed for professionals along the IT corridor",
            "Premium finishes and elevated amenities (demo framing)",
            "Priority site visits for early registrants",
        ],
        "education": (
            "Casagrand Mercury targets buyers who want a premium apartment "
            "experience with work-friendly amenities near the OMR corridor. "
            "It emphasizes elevated club facilities and contemporary living."
        ),
        "site_visit_note": (
            "Mercury early tour slots are limited. We can reserve a visit "
            "and share a callback from the sales desk."
        ),
    },
}


def list_projects() -> list[dict[str, Any]]:
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "city": p["city"],
            "status": p["status"],
        }
        for p in PROJECTS.values()
    ]


def get_project(project_id: str) -> dict[str, Any] | None:
    return PROJECTS.get(project_id.lower())


def resolve_project_alias(text: str) -> str | None:
    lowered = text.lower()
    aliases = {
        "highcity": ["highcity", "high city", "ஹைசிட்டி"],
        "avenuepark": ["avenuepark", "avenue park", "avenue", "அவென்யூ"],
        "mercury": ["mercury", "மெர்க்குரி", "மெர்குரி"],
    }
    for project_id, terms in aliases.items():
        if any(term in lowered for term in terms):
            return project_id
    return None
