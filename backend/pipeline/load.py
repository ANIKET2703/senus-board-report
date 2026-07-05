"""Seed the database from validated extraction output (data/extracted/facts.json)."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from app.core.config import get_settings
from app.core.db import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import Document, FinancialFact, Period, User, ValidationResult
from pipeline.validate import run_checks

ROOT = Path(__file__).resolve().parents[2]


def seed_database() -> None:
    Base.metadata.create_all(engine)
    payload = json.loads((ROOT / "data" / "extracted" / "facts.json").read_text())

    with SessionLocal() as db:
        if db.query(Document).count():
            print("database already seeded — skipping (drop DB to reseed)")
            return

        doc_ids = {}
        for d in payload["documents"]:
            doc = Document(filename=d["filename"], title=d["title"], doc_type=d["doc_type"],
                           published_date=date.fromisoformat(d["published_date"]),
                           pages=d["pages"], has_text_layer=d["has_text_layer"])
            db.add(doc)
            db.flush()
            doc_ids[d["id"]] = doc.id

        period_ids = {}
        for p in payload["periods"]:
            period = Period(label=p["label"], start_date=date.fromisoformat(p["start_date"]),
                            end_date=date.fromisoformat(p["end_date"]),
                            period_type=p["period_type"], audited=p["audited"])
            db.add(period)
            db.flush()
            period_ids[p["label"]] = period.id

        for f in payload["facts"]:
            db.add(FinancialFact(
                period_id=period_ids[f["period"]], document_id=doc_ids[f["doc"]],
                statement=f["statement"], line_code=f["line_code"], label=f["label"],
                value=f["value"], unit=f.get("unit", "EUR"), page_number=f.get("page"),
                extraction_method=f.get("method", "vision"), confidence=f.get("confidence", 1.0)))

        by_period: dict[str, dict[str, float]] = {}
        for f in payload["facts"]:
            by_period.setdefault(f["period"], {})[f["line_code"]] = f["value"]
        for c in run_checks(by_period):
            db.add(ValidationResult(**c))

        settings = get_settings()
        db.add(User(email=settings.demo_user_email,
                    hashed_password=hash_password(settings.demo_user_password),
                    full_name="Brendan Allen (demo)"))
        db.commit()
        print(f"seeded {len(payload['facts'])} facts, {len(payload['documents'])} documents")
