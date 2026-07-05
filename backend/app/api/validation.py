from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.core.db import get_db
from app.core.security import get_current_user
from app.models import FinancialFact, ValidationResult

router = APIRouter(prefix="/api/validation", tags=["validation"],
                   dependencies=[Depends(get_current_user)])

# facts extracted below this confidence require a human sign-off before use
CONFIDENCE_REVIEW_THRESHOLD = 0.9


@router.get("")
def validation_results(db: Session = Depends(get_db)):
    rows = db.query(ValidationResult).all()
    return {"summary": {
        "pass": sum(1 for r in rows if r.status == "pass"),
        "warn": sum(1 for r in rows if r.status == "warn"),
        "fail": sum(1 for r in rows if r.status == "fail")},
        "checks": [{"check": r.check_name, "period": r.period_label,
                    "status": r.status, "detail": r.detail} for r in rows]}


@router.get("/review-queue")
def review_queue(db: Session = Depends(get_db)):
    """Human-in-the-loop queue: facts whose extraction confidence is below the
    review threshold (two-pass verification failed or was inconclusive)."""
    facts = (db.query(FinancialFact)
             .options(joinedload(FinancialFact.period), joinedload(FinancialFact.document))
             .filter(FinancialFact.confidence < CONFIDENCE_REVIEW_THRESHOLD)
             .order_by(FinancialFact.confidence).all())
    return {"threshold": CONFIDENCE_REVIEW_THRESHOLD,
            "items": [{"id": f.id, "period": f.period.label, "line_code": f.line_code,
                       "label": f.label, "value": float(f.value), "page": f.page_number,
                       "document": f.document.title, "method": f.extraction_method,
                       "confidence": f.confidence} for f in facts]}
