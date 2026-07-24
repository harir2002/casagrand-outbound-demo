"""Load Casagrand KB from Hugging Face datasets or local seed."""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.kb.schema import EscalationRule, FAQCard, ProjectCard
from app.kb.seed_builder import (
    build_escalation_rules,
    build_faq_cards,
    build_kb_documents,
    build_project_cards,
)

logger = get_logger(__name__)


def load_local_seed() -> tuple[list[ProjectCard], list[FAQCard], list[EscalationRule]]:
    projects = build_project_cards()
    faqs = build_faq_cards()
    escalations = build_escalation_rules()
    logger.info(
        "kb_local_seed loaded projects=%s faqs=%s escalations=%s docs=%s",
        len(projects),
        len(faqs),
        len(escalations),
        len(build_kb_documents(projects, faqs, escalations)),
    )
    return projects, faqs, escalations


def load_hf_dataset(
    dataset_id: str,
    *,
    split: str = "train",
) -> tuple[list[ProjectCard], list[FAQCard], list[EscalationRule]] | None:
    """Load and normalize an HF dataset. Returns None on failure."""
    if not dataset_id.strip():
        return None
    try:
        from datasets import load_dataset  # type: ignore
    except ImportError:
        logger.warning(
            "kb_hf_skip reason=datasets_not_installed dataset_id=%s",
            dataset_id,
        )
        return None

    try:
        ds = load_dataset(dataset_id, split=split)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "kb_hf_load_failed dataset_id=%s error=%s; using local seed",
            dataset_id,
            exc,
        )
        return None

    projects: list[ProjectCard] = []
    faqs: list[FAQCard] = []
    escalations: list[EscalationRule] = []

    for row in ds:
        record = _row_to_dict(row)
        record_type = str(record.get("record_type") or record.get("type") or "").lower()
        try:
            if record_type == "project":
                projects.append(_normalize_project(record))
            elif record_type == "faq":
                faqs.append(_normalize_faq(record))
            elif record_type in {"escalation", "escalation_rule"}:
                escalations.append(_normalize_escalation(record))
        except Exception as exc:  # noqa: BLE001
            logger.warning("kb_hf_row_skip error=%s row_keys=%s", exc, list(record.keys()))

    if not projects and not faqs:
        logger.warning("kb_hf_empty dataset_id=%s; using local seed", dataset_id)
        return None

    # Fill gaps from local seed so demo never loses approved cards.
    local_projects, local_faqs, local_escalations = load_local_seed()
    if not projects:
        projects = local_projects
    if not faqs:
        faqs = local_faqs
    if not escalations:
        escalations = local_escalations

    logger.info(
        "kb_hf_loaded dataset_id=%s projects=%s faqs=%s escalations=%s",
        dataset_id,
        len(projects),
        len(faqs),
        len(escalations),
    )
    return projects, faqs, escalations


def load_knowledge_base(
    dataset_id: str = "",
    *,
    split: str = "train",
) -> tuple[list[ProjectCard], list[FAQCard], list[EscalationRule], str]:
    """Return normalized KB + source label (`hf:<id>` or `local_seed`)."""
    if dataset_id.strip():
        loaded = load_hf_dataset(dataset_id, split=split)
        if loaded is not None:
            return (*loaded, f"hf:{dataset_id}")
    return (*load_local_seed(), "local_seed")


def _row_to_dict(row: Any) -> dict[str, Any]:
    if isinstance(row, dict):
        return dict(row)
    try:
        return dict(row)
    except Exception:  # noqa: BLE001
        return {k: row[k] for k in getattr(row, "keys", lambda: [])()}


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str):
        parts = [p.strip() for p in value.split(",")]
        return [p for p in parts if p]
    return [str(value)]


def _normalize_project(record: dict[str, Any]) -> ProjectCard:
    project_id = str(record.get("project_id") or record.get("id") or "").lower()
    return ProjectCard(
        project_id=project_id,
        name=str(record.get("name") or project_id),
        city=str(record.get("city") or ""),
        location=str(record.get("location") or ""),
        status=str(record.get("status") or ""),
        typology=str(record.get("typology") or ""),
        pricing_from=str(record.get("pricing_from") or record.get("pricing") or ""),
        amenities=_as_list(record.get("amenities")),
        highlights=_as_list(record.get("highlights")),
        education=str(record.get("education") or record.get("body") or ""),
        site_visit_note=str(record.get("site_visit_note") or ""),
        brochure_note=str(record.get("brochure_note") or ""),
        language=str(record.get("language") or "en"),
        aliases=_as_list(record.get("aliases")),
    )


def _normalize_faq(record: dict[str, Any]) -> FAQCard:
    project_id = str(record.get("project_id") or "highcity").lower()
    intent = str(record.get("intent") or record.get("category") or "project_info")
    language = str(record.get("language") or "en")
    faq_id = str(record.get("faq_id") or f"{project_id}:{intent}:{language}")
    return FAQCard(
        faq_id=faq_id,
        project_id=project_id,
        intent=intent,
        category=str(record.get("category") or intent),
        language=language,
        question=str(record.get("question") or record.get("title") or intent),
        answer=str(record.get("answer") or record.get("body") or record.get("text") or ""),
        source=str(record.get("source") or f"hf:{faq_id}"),
    )


def _normalize_escalation(record: dict[str, Any]) -> EscalationRule:
    language = str(record.get("language") or "en")
    trigger = str(record.get("trigger") or "human_handoff")
    return EscalationRule(
        rule_id=str(record.get("rule_id") or f"{trigger}:{language}"),
        trigger=trigger,
        action=str(record.get("action") or "handoff"),
        language=language,
        message=str(record.get("message") or record.get("body") or ""),
        reason=str(record.get("reason") or trigger),
    )
