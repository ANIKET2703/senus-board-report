from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models import Period
from app.services.facts_repo import facts_by_period
from app.services.valuation import compute_valuation

router = APIRouter(prefix="/api/valuation", tags=["valuation"],
                   dependencies=[Depends(get_current_user)])


@router.get("")
def valuation(db: Session = Depends(get_db)):
    mkt = db.query(Period).filter_by(label="MKT").first()
    return compute_valuation(facts_by_period(db),
                             as_of=str(mkt.end_date) if mkt else None)
