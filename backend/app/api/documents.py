from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models import Document, FinancialFact

router = APIRouter(prefix="/api/documents", tags=["documents"],
                   dependencies=[Depends(get_current_user)])

ROOT = Path(__file__).resolve().parents[3]
SOURCE_DIR = ROOT / "data" / "source_documents"


@router.get("")
def documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.published_date).all()
    return [{"id": d.id, "filename": d.filename, "title": d.title, "doc_type": d.doc_type,
             "published_date": str(d.published_date), "pages": d.pages,
             "has_text_layer": d.has_text_layer,
             "facts_extracted": db.query(FinancialFact).filter_by(document_id=d.id).count()}
            for d in docs]


@router.get("/{doc_id}/pdf")
def document_pdf(doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404)
    path = SOURCE_DIR / doc.filename
    if not path.exists():
        raise HTTPException(404, "source PDF not present in this deployment")
    return FileResponse(path, media_type="application/pdf", filename=doc.filename)


@router.get("/{doc_id}/facts")
def document_facts(doc_id: int, db: Session = Depends(get_db)):
    facts = (db.query(FinancialFact).filter_by(document_id=doc_id)
             .order_by(FinancialFact.page_number).all())
    return [{"id": f.id, "period": f.period.label, "statement": f.statement,
             "label": f.label, "value": float(f.value), "page": f.page_number,
             "method": f.extraction_method, "confidence": f.confidence} for f in facts]
