from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models import Period
from app.services.facts_repo import statement_rows

router = APIRouter(prefix="/api/statements", tags=["statements"],
                   dependencies=[Depends(get_current_user)])

VALID = {"pnl", "bs", "cf", "kpi"}


@router.get("/periods")
def periods(db: Session = Depends(get_db)):
    return [{"label": p.label, "start": str(p.start_date), "end": str(p.end_date),
             "type": p.period_type, "audited": p.audited}
            for p in db.query(Period).order_by(Period.start_date).all()]


@router.get("/{statement}")
def statement(statement: str, db: Session = Depends(get_db)):
    if statement not in VALID:
        raise HTTPException(404, f"statement must be one of {sorted(VALID)}")
    return statement_rows(db, statement)
