from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user
from app.services.scenario import project

router = APIRouter(prefix="/api/scenario", tags=["scenario"],
                   dependencies=[Depends(get_current_user)])


@router.get("")
def scenario(growth: float = Query(0.50, ge=-0.5, le=3.0),
             gross_margin: float = Query(0.7748, ge=0.1, le=0.95),
             opex_growth: float = Query(0.18, ge=-0.5, le=2.0)):
    return project(growth_rate=growth, gross_margin=gross_margin, opex_growth=opex_growth)
