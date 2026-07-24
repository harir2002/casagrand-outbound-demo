"""In-memory repository for project cards, FAQ cards, and escalation rules."""

from __future__ import annotations

from app.kb.schema import EscalationRule, FAQCard, ProjectCard


class KnowledgeRepository:
    def __init__(
        self,
        projects: list[ProjectCard],
        faqs: list[FAQCard],
        escalations: list[EscalationRule],
        *,
        source: str = "local_seed",
    ) -> None:
        self.source = source
        self._projects = {p.project_id.lower(): p for p in projects}
        self._faqs = list(faqs)
        self._escalations = list(escalations)
        self._faqs_by_key: dict[tuple[str, str, str], FAQCard] = {}
        for faq in faqs:
            key = (faq.project_id.lower(), faq.intent.lower(), faq.language.lower())
            self._faqs_by_key[key] = faq

    def list_projects(self) -> list[ProjectCard]:
        return list(self._projects.values())

    def get_project(self, project_id: str) -> ProjectCard | None:
        return self._projects.get(project_id.lower())

    def get_faq(
        self,
        project_id: str,
        intent: str,
        language: str,
    ) -> FAQCard | None:
        return self._faqs_by_key.get(
            (project_id.lower(), intent.lower(), language.lower())
        )

    def list_faqs(
        self,
        *,
        project_id: str | None = None,
        intent: str | None = None,
        language: str | None = None,
    ) -> list[FAQCard]:
        rows = self._faqs
        if project_id:
            rows = [f for f in rows if f.project_id.lower() == project_id.lower()]
        if intent:
            rows = [f for f in rows if f.intent.lower() == intent.lower()]
        if language:
            rows = [f for f in rows if f.language.lower() == language.lower()]
        return list(rows)

    def get_escalation(self, trigger: str, language: str) -> EscalationRule | None:
        trigger_l = trigger.lower()
        language_l = language.lower()
        for rule in self._escalations:
            if rule.trigger.lower() == trigger_l and rule.language.lower() == language_l:
                return rule
        for rule in self._escalations:
            if rule.trigger.lower() == trigger_l:
                return rule
        return None

    def comparison_cards(self, project_ids: list[str] | None = None) -> list[ProjectCard]:
        if not project_ids:
            return self.list_projects()
        cards: list[ProjectCard] = []
        for pid in project_ids:
            card = self.get_project(pid)
            if card is not None:
                cards.append(card)
        return cards
