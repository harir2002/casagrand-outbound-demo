"""Build the local seed corpus from approved project/FAQ templates.

This mirrors the planned Hugging Face dataset shape so Spaces can either:
  - load from HF (`HF_DATASET_ID`), or
  - rebuild from this deterministic local seed.
"""

from __future__ import annotations

from app.data.faq_data import (
    HANDOFF_REPLY,
    SAFE_FALLBACK,
    approved_answer_for,
    build_education,
    build_introduction,
)
from app.data.projects import PROJECT_ALIASES, PROJECTS_VERSION, list_projects, get_project
from app.kb.schema import EscalationRule, FAQCard, KBDocument, ProjectCard
from app.models.session import Intent, Language


_FAQ_INTENTS = (
    Intent.PROJECT_INFO,
    Intent.PRICING,
    Intent.LOCATION,
    Intent.AMENITIES,
    Intent.SITE_VISIT,
    Intent.CALLBACK,
    Intent.BROCHURE,
)

_LANGUAGES = (Language.EN, Language.TA, Language.TANGLISH)


def build_project_cards() -> list[ProjectCard]:
    cards: list[ProjectCard] = []
    for summary in list_projects():
        project = get_project(summary.id)
        if project is None:
            continue
        cards.append(
            ProjectCard(
                project_id=project.id,
                name=project.name,
                city=project.city,
                location=project.location,
                status=project.status,
                typology=project.typology,
                pricing_from=project.pricing_from,
                amenities=list(project.amenities),
                highlights=list(project.highlights),
                education=project.education,
                site_visit_note=project.site_visit_note,
                brochure_note=project.brochure_note,
                language="en",
                aliases=list(PROJECT_ALIASES.get(project.id, [])),
            )
        )
    return cards


def build_faq_cards() -> list[FAQCard]:
    cards: list[FAQCard] = []
    for summary in list_projects():
        project_id = summary.id
        for language in _LANGUAGES:
            for intent in _FAQ_INTENTS:
                approved = approved_answer_for(intent, project_id, language)
                if approved is None:
                    continue
                answer, source = approved
                cards.append(
                    FAQCard(
                        faq_id=f"{project_id}:{intent.value}:{language.value}",
                        project_id=project_id,
                        intent=intent.value,
                        category=intent.value,
                        language=language.value,
                        question=_question_for(intent, language),
                        answer=answer,
                        source=source,
                    )
                )
            intro_text, intro_source = build_introduction(project_id, language)
            cards.append(
                FAQCard(
                    faq_id=f"{project_id}:greeting:{language.value}",
                    project_id=project_id,
                    intent=Intent.GREETING.value,
                    category="greeting",
                    language=language.value,
                    question="hello / vanakkam",
                    answer=intro_text,
                    source=intro_source,
                )
            )
            edu_text, edu_source = build_education(project_id, language)
            cards.append(
                FAQCard(
                    faq_id=f"{project_id}:education:{language.value}",
                    project_id=project_id,
                    intent="brochure_summary",
                    category="brochure",
                    language=language.value,
                    question="brochure summary / project overview",
                    answer=edu_text,
                    source=edu_source,
                )
            )
            cards.append(
                FAQCard(
                    faq_id=f"{project_id}:ood:{language.value}",
                    project_id=project_id,
                    intent=Intent.OUT_OF_DOMAIN.value,
                    category="fallback",
                    language=language.value,
                    question="out of domain",
                    answer=SAFE_FALLBACK[language],
                    source=f"projects@{PROJECTS_VERSION}:{project_id}:safe_fallback",
                )
            )
    return cards


def build_escalation_rules() -> list[EscalationRule]:
    rules: list[EscalationRule] = []
    for language in _LANGUAGES:
        rules.append(
            EscalationRule(
                rule_id=f"handoff:{language.value}",
                trigger="human_handoff",
                action="handoff",
                language=language.value,
                message=HANDOFF_REPLY[language],
                reason="caller_requested_human",
            )
        )
        rules.append(
            EscalationRule(
                rule_id=f"ood_escalation:{language.value}",
                trigger="out_of_domain",
                action="safe_fallback",
                language=language.value,
                message=SAFE_FALLBACK[language],
                reason="out_of_domain_topic",
            )
        )
    return rules


def build_kb_documents(
    projects: list[ProjectCard] | None = None,
    faqs: list[FAQCard] | None = None,
    escalations: list[EscalationRule] | None = None,
) -> list[KBDocument]:
    projects = projects if projects is not None else build_project_cards()
    faqs = faqs if faqs is not None else build_faq_cards()
    escalations = escalations if escalations is not None else build_escalation_rules()
    docs: list[KBDocument] = []

    for project in projects:
        brochure = (
            f"{project.name}. {project.education} "
            f"Location: {project.location}. Typology: {project.typology}. "
            f"Pricing: {project.pricing_from}. "
            f"Amenities: {', '.join(project.amenities)}. "
            f"Highlights: {'; '.join(project.highlights)}."
        )
        docs.append(
            KBDocument(
                doc_id=f"project:{project.project_id}:brochure",
                record_type="project",
                project_id=project.project_id,
                intent="brochure_summary",
                category="brochure",
                language=project.language or "en",
                title=f"{project.name} brochure",
                text=brochure,
                metadata={"name": project.name, "source": f"projects@{PROJECTS_VERSION}"},
            )
        )
        compare_blob = (
            f"Compare {project.name}: {project.typology} at {project.location}, "
            f"status {project.status}, from {project.pricing_from}."
        )
        docs.append(
            KBDocument(
                doc_id=f"project:{project.project_id}:comparison",
                record_type="comparison",
                project_id=project.project_id,
                intent="comparison",
                category="comparison",
                language="en",
                title=f"{project.name} comparison card",
                text=compare_blob,
                metadata={"name": project.name, "pricing_from": project.pricing_from},
            )
        )

    for faq in faqs:
        docs.append(
            KBDocument(
                doc_id=f"faq:{faq.faq_id}",
                record_type="faq",
                project_id=faq.project_id,
                intent=faq.intent,
                category=faq.category,
                language=faq.language,
                title=faq.question,
                text=f"Q: {faq.question}\nA: {faq.answer}",
                metadata={"source": faq.source, "answer": faq.answer},
            )
        )

    for rule in escalations:
        docs.append(
            KBDocument(
                doc_id=f"escalation:{rule.rule_id}",
                record_type="escalation",
                project_id="",
                intent=rule.trigger,
                category="escalation",
                language=rule.language,
                title=rule.trigger,
                text=rule.message,
                metadata={"action": rule.action, "reason": rule.reason},
            )
        )

    return docs


def _question_for(intent: Intent, language: Language) -> str:
    en = {
        Intent.PROJECT_INFO: "Tell me about the project",
        Intent.PRICING: "What is the pricing?",
        Intent.LOCATION: "Where is the project located?",
        Intent.AMENITIES: "What amenities are available?",
        Intent.SITE_VISIT: "Can I book a site visit?",
        Intent.CALLBACK: "Please arrange a callback",
        Intent.BROCHURE: "Please send the brochure",
    }
    ta = {
        Intent.PROJECT_INFO: "திட்டம் பற்றி சொல்லுங்கள்",
        Intent.PRICING: "விலை என்ன?",
        Intent.LOCATION: "இடம் எங்கே?",
        Intent.AMENITIES: "வசதிகள் என்ன?",
        Intent.SITE_VISIT: "தள வருகை புக் செய்யலாமா?",
        Intent.CALLBACK: "கால்பேக் ஏற்பாடு செய்யுங்கள்",
        Intent.BROCHURE: "brochure அனுப்புங்கள்",
    }
    tanglish = {
        Intent.PROJECT_INFO: "project pathi sollunga",
        Intent.PRICING: "pricing evlo?",
        Intent.LOCATION: "location enge?",
        Intent.AMENITIES: "amenities enna?",
        Intent.SITE_VISIT: "site visit book pannalama?",
        Intent.CALLBACK: "callback arrange pannunga",
        Intent.BROCHURE: "brochure anuppunga",
    }
    table = {Language.EN: en, Language.TA: ta, Language.TANGLISH: tanglish}
    return table[language].get(intent, intent.value)
