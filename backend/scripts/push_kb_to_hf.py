"""Export local approved KB seed and push to Hugging Face dataset.

Usage (from backend/):
  .\\.venv\\Scripts\\python.exe scripts\\push_kb_to_hf.py

Default target: Harir2002/casagrand_projects_faq
Override with:  $env:HF_DATASET_ID='username/repo'
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.kb.seed_builder import (  # noqa: E402
    build_escalation_rules,
    build_faq_cards,
    build_kb_documents,
    build_project_cards,
)

# Flat schema so Dataset.from_list accepts mixed record types.
_COLUMNS = [
    "record_type",
    "project_id",
    "name",
    "city",
    "location",
    "status",
    "typology",
    "pricing_from",
    "amenities",
    "highlights",
    "education",
    "site_visit_note",
    "brochure_note",
    "language",
    "aliases",
    "faq_id",
    "intent",
    "category",
    "question",
    "answer",
    "source",
    "rule_id",
    "trigger",
    "action",
    "message",
    "reason",
]


def _blank() -> dict:
    return {
        "record_type": "",
        "project_id": "",
        "name": "",
        "city": "",
        "location": "",
        "status": "",
        "typology": "",
        "pricing_from": "",
        "amenities": [],
        "highlights": [],
        "education": "",
        "site_visit_note": "",
        "brochure_note": "",
        "language": "en",
        "aliases": [],
        "faq_id": "",
        "intent": "",
        "category": "",
        "question": "",
        "answer": "",
        "source": "",
        "rule_id": "",
        "trigger": "",
        "action": "",
        "message": "",
        "reason": "",
    }


def _rows() -> list[dict]:
    projects = build_project_cards()
    faqs = build_faq_cards()
    escalations = build_escalation_rules()
    docs = build_kb_documents(projects, faqs, escalations)

    rows: list[dict] = []
    for p in projects:
        row = _blank()
        row.update(p.model_dump())
        row["record_type"] = "project"
        rows.append(row)

    for f in faqs:
        row = _blank()
        row.update(f.model_dump())
        row["record_type"] = "faq"
        rows.append(row)

    for e in escalations:
        row = _blank()
        row.update(e.model_dump())
        row["record_type"] = "escalation"
        rows.append(row)

    # Keep column order stable.
    rows = [{k: r.get(k, _blank()[k]) for k in _COLUMNS} for r in rows]

    print(
        f"seed rows: projects={len(projects)} faqs={len(faqs)} "
        f"escalations={len(escalations)} total={len(rows)} "
        f"(rag_docs={len(docs)})"
    )
    return rows


def main() -> int:
    dataset_id = (
        os.getenv("HF_DATASET_ID", "").strip() or "Harir2002/casagrand_projects_faq"
    )
    out_dir = ROOT / "data" / "hf_kb"
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "train.jsonl"

    rows = _rows()
    with jsonl_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {jsonl_path} ({jsonl_path.stat().st_size} bytes)")

    from datasets import Dataset  # type: ignore

    ds = Dataset.from_list(rows)
    print(f"pushing to hf://datasets/{dataset_id} split=train ...")
    ds.push_to_hub(dataset_id, split="train", private=False)
    print(f"DONE: https://huggingface.co/datasets/{dataset_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
