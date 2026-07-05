from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.services.facts_repo import facts_by_period
from app.services.metrics_engine import compute_all, ebitda_to_fcf_bridge

router = APIRouter(prefix="/api/metrics", tags=["metrics"],
                   dependencies=[Depends(get_current_user)])


@router.get("")
def all_metrics(db: Session = Depends(get_db)):
    return compute_all(facts_by_period(db))


@router.get("/fcf-bridge/{period}")
def fcf_bridge(period: str, db: Session = Depends(get_db)):
    facts = facts_by_period(db).get(period.upper(), {})
    return ebitda_to_fcf_bridge(facts, period.upper())
