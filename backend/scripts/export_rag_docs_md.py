"""Generate docs/rag-knowledge-base.md from the approved local KB seed."""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))

from app.kb.seed_builder import (  # noqa: E402
    build_escalation_rules,
    build_faq_cards,
    build_kb_documents,
    build_project_cards,
)


def main() -> int:
    projects = build_project_cards()
    faqs = build_faq_cards()
    escalations = build_escalation_rules()
    docs = build_kb_documents(projects, faqs, escalations)

    out = REPO / "docs" / "rag-knowledge-base.md"
    lines: list[str] = []

    lines.append("# Casagrand RAG Knowledge Base")
    lines.append("")
    lines.append(
        "Approved knowledge used by the outbound voice agent for RAG retrieval."
    )
    lines.append("")
    lines.append("| Item | Count |")
    lines.append("|---|---:|")
    lines.append(f"| Projects | {len(projects)} |")
    lines.append(f"| FAQ cards | {len(faqs)} |")
    lines.append(f"| Escalation rules | {len(escalations)} |")
    lines.append(f"| Indexed RAG documents | {len(docs)} |")
    lines.append("| Languages | English, Tamil, Tanglish |")
    lines.append(
        "| Source | Local seed + Hugging Face "
        "`Harir2002/casagrand_projects_faq` |"
    )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Table of contents")
    lines.append("")
    lines.append("1. [Project cards](#1-project-cards)")
    lines.append("2. [FAQ cards](#2-faq-cards)")
    lines.append("3. [Escalation rules](#3-escalation-rules)")
    lines.append("4. [Indexed RAG documents](#4-indexed-rag-documents)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. Project cards")
    lines.append("")

    for p in projects:
        lines.append(f"### {p.name} (`{p.project_id}`)")
        lines.append("")
        lines.append(f"- **City:** {p.city}")
        lines.append(f"- **Location:** {p.location}")
        lines.append(f"- **Status:** {p.status}")
        lines.append(f"- **Typology:** {p.typology}")
        lines.append(f"- **Pricing from:** {p.pricing_from}")
        lines.append(f"- **Language:** {p.language}")
        if p.aliases:
            alias_text = ", ".join(p.aliases)
            lines.append(f"- **Aliases:** {alias_text}")
        lines.append("")
        lines.append("**Amenities**")
        lines.append("")
        for a in p.amenities:
            lines.append(f"- {a}")
        lines.append("")
        lines.append("**Highlights**")
        lines.append("")
        for h in p.highlights:
            lines.append(f"- {h}")
        lines.append("")
        lines.append("**Education**")
        lines.append("")
        lines.append(p.education or "_None_")
        lines.append("")
        lines.append("**Site visit note**")
        lines.append("")
        lines.append(p.site_visit_note or "_None_")
        lines.append("")
        lines.append("**Brochure note**")
        lines.append("")
        lines.append(p.brochure_note or "_None_")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 2. FAQ cards")
    lines.append("")
    lines.append("Grouped by project, then language, then intent.")
    lines.append("")

    by_project: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for f in faqs:
        by_project[f.project_id][f.language].append(f)

    project_names = {p.project_id: p.name for p in projects}
    for project_id in ["highcity", "avenuepark", "mercury"]:
        lines.append(f"### {project_names.get(project_id, project_id)}")
        lines.append("")
        for language in ["en", "ta", "tanglish"]:
            cards = by_project[project_id].get(language, [])
            if not cards:
                continue
            lines.append(f"#### Language: `{language}`")
            lines.append("")
            for f in sorted(cards, key=lambda x: (x.intent, x.faq_id)):
                lines.append(f"##### {f.intent} — `{f.faq_id}`")
                lines.append("")
                lines.append(f"- **Category:** {f.category}")
                lines.append(f"- **Source:** `{f.source}`")
                lines.append(f"- **Question:** {f.question}")
                lines.append("")
                lines.append("**Answer**")
                lines.append("")
                lines.append(f.answer)
                lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## 3. Escalation rules")
    lines.append("")
    for e in escalations:
        lines.append(f"### `{e.rule_id}`")
        lines.append("")
        lines.append(f"- **Trigger:** {e.trigger}")
        lines.append(f"- **Action:** {e.action}")
        lines.append(f"- **Language:** {e.language}")
        lines.append(f"- **Reason:** {e.reason}")
        lines.append("")
        lines.append("**Message**")
        lines.append("")
        lines.append(e.message)
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 4. Indexed RAG documents")
    lines.append("")
    lines.append(
        "These are the chunks placed into the vector/memory index at startup."
    )
    lines.append("")

    by_type: dict[str, list] = defaultdict(list)
    for d in docs:
        by_type[d.record_type].append(d)

    for record_type in ["project", "comparison", "faq", "escalation"]:
        chunk_list = by_type.get(record_type, [])
        if not chunk_list:
            continue
        lines.append(f"### Record type: `{record_type}` ({len(chunk_list)})")
        lines.append("")
        for d in chunk_list:
            lines.append(f"#### `{d.doc_id}`")
            lines.append("")
            lines.append(f"- **Project:** {d.project_id or '—'}")
            lines.append(f"- **Intent:** {d.intent or '—'}")
            lines.append(f"- **Category:** {d.category or '—'}")
            lines.append(f"- **Language:** {d.language}")
            lines.append(f"- **Title:** {d.title or '—'}")
            if d.metadata:
                meta = ", ".join(f"{k}={v}" for k, v in d.metadata.items())
                lines.append(f"- **Metadata:** {meta}")
            lines.append("")
            lines.append("**Text**")
            lines.append("")
            lines.append(d.text)
            lines.append("")

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
