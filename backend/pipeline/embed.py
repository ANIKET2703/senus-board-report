"""Chunk documents and store retrieval vectors.

Small corpus (7 PDFs) => local embeddings (fastembed/bge-small) are ample;
no second API vendor needed. If fastembed isn't installed the system falls
back to BM25 at query time (app/services/rag.py) — chunks are stored either way.
"""
from __future__ import annotations

import json
from pathlib import Path

import pdfplumber

from app.core.db import Base, SessionLocal, engine
from app.models import Chunk, Document

ROOT = Path(__file__).resolve().parents[2]
CHUNK_CHARS = 1400


def _chunks_from_text(text: str) -> list[str]:
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    chunks, current = [], ""
    for p in paras:
        if len(current) + len(p) > CHUNK_CHARS and current:
            chunks.append(current)
            current = ""
        current += p + "\n"
    if current.strip():
        chunks.append(current)
    return chunks


def embed_documents() -> None:
    Base.metadata.create_all(engine)
    try:
        from fastembed import TextEmbedding
        embedder = TextEmbedding("BAAI/bge-small-en-v1.5")
    except ImportError:
        embedder = None
        print("fastembed not installed — storing chunks without vectors (BM25 fallback)")

    with SessionLocal() as db:
        if db.query(Chunk).count():
            print("chunks already present — skipping")
            return
        docs = {d.filename: d for d in db.query(Document).all()}
        for pdf_path in sorted((ROOT / "data" / "source_documents").glob("*.pdf")):
            doc = docs.get(pdf_path.name)
            if not doc:
                continue
            with pdfplumber.open(pdf_path) as pdf:
                for page_no, page in enumerate(pdf.pages, 1):
                    text = page.extract_text() or ""
                    # release the parsed page layout immediately: pdfplumber caches
                    # every page it touches, which blows past small-instance RAM
                    # (512MB) on the larger filings
                    if hasattr(page, "flush_cache"):
                        page.flush_cache()
                    if len(text.strip()) < 40:
                        continue
                    for chunk_text in _chunks_from_text(text):
                        emb = None
                        if embedder:
                            emb = json.dumps(list(map(float, next(iter(embedder.embed([chunk_text]))))))
                        db.add(Chunk(document_id=doc.id, page_number=page_no,
                                     content=chunk_text, embedding_json=emb))
            db.commit()  # commit per document to keep the session small
        print(f"stored {db.query(Chunk).count()} chunks")
