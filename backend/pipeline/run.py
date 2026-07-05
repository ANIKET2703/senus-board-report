"""Pipeline entrypoint.

  python -m pipeline.run --extract    re-run AI extraction (needs ANTHROPIC_API_KEY)
  python -m pipeline.run --validate   run accounting-identity checks on facts.json
  python -m pipeline.run --seed       load validated facts into the database
  python -m pipeline.run --embed      chunk + embed documents for RAG

The committed data/extracted/facts.json is the human-validated merge of the
per-document extraction outputs (see README: 'How outputs were validated').
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"


def load_facts_by_period() -> dict:
    payload = json.loads((DATA / "extracted" / "facts.json").read_text())
    by_period: dict[str, dict[str, float]] = {}
    for f in payload["facts"]:
        by_period.setdefault(f["period"], {})[f["line_code"]] = f["value"]
    return by_period


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--seed", action="store_true")
    parser.add_argument("--embed", action="store_true")
    args = parser.parse_args()

    if args.extract:
        from pipeline.extract import extract_all
        extract_all(DATA / "source_documents", DATA / "extracted" / "raw")

    if args.validate:
        from pipeline.validate import run_checks
        checks = run_checks(load_facts_by_period())
        for c in checks:
            print(f"[{c['status'].upper():4}] {c['check_name']} ({c['period_label']}): {c['detail']}")
        fails = [c for c in checks if c["status"] == "fail"]
        print(f"\n{len(checks)} checks: {len(checks) - len(fails)} pass/warn, {len(fails)} fail")

    if args.seed:
        from pipeline.load import seed_database
        seed_database()

    if args.embed:
        from pipeline.embed import embed_documents
        embed_documents()


if __name__ == "__main__":
    main()
