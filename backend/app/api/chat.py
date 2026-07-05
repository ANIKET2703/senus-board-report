from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.services.facts_repo import metrics_context_string
from app.services.rag import answer

router = APIRouter(prefix="/api/chat", tags=["chat"],
                   dependencies=[Depends(get_current_user)])


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@router.post("")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    return answer(db, req.question, metrics_context_string(db))
