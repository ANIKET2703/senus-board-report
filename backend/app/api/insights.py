from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.services.facts_repo import metrics_context_string
from app.services.insights import AUDIENCE_FRAMING, get_or_generate

router = APIRouter(prefix="/api/insights", tags=["insights"],
                   dependencies=[Depends(get_current_user)])

SECTIONS = {"overview", "growth", "profitability", "cash", "solvency", "returns",
            "valuation", "outlook"}


@router.get("/{audience}/{section}")
def insight(audience: str, section: str, period: str = "HY26",
            db: Session = Depends(get_db)):
    if audience not in AUDIENCE_FRAMING:
        raise HTTPException(404, f"audience must be one of {sorted(AUDIENCE_FRAMING)}")
    if section not in SECTIONS:
        raise HTTPException(404, f"section must be one of {sorted(SECTIONS)}")
    return get_or_generate(db, audience, section, period, metrics_context_string(db))
