"""Ask-the-Board-Pack: retrieval-augmented Q&A with page-level citations.

Retrieval: cosine over stored fastembed vectors when available, else BM25.
Generation: Claude answers ONLY from retrieved passages + the validated
metrics table, and must cite [doc, page] for every claim.
"""
from __future__ import annotations

import json
import math

from sqlalchemy.orm import Session

from app.models import Chunk, Document

TOP_K = 6

_EMBEDDER = None  # loaded once per process; model init is expensive


def _get_embedder():
    global _EMBEDDER
    if _EMBEDDER is None:
        from fastembed import TextEmbedding
        _EMBEDDER = TextEmbedding("BAAI/bge-small-en-v1.5")
    return _EMBEDDER


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def retrieve(db: Session, query: str, top_k: int = TOP_K) -> list[dict]:
    chunks = db.query(Chunk).all()
    if not chunks:
        return []
    scored: list[tuple[float, Chunk]] = []

    with_vectors = [c for c in chunks if c.embedding_json]
    if with_vectors:
        try:
            embedder = _get_embedder()
            qv = list(map(float, next(iter(embedder.embed([query])))))
            scored = [(_cosine(qv, json.loads(c.embedding_json)), c) for c in with_vectors]
        except ImportError:
            pass

    if not scored:  # BM25 fallback, plenty for a 7-document corpus
        from rank_bm25 import BM25Okapi
        tokenised = [c.content.lower().split() for c in chunks]
        bm25 = BM25Okapi(tokenised)
        scores = bm25.get_scores(query.lower().split())
        scored = list(zip(scores, chunks))

    scored.sort(key=lambda t: t[0], reverse=True)
    docs = {d.id: d for d in db.query(Document).all()}
    return [{
        "content": c.content,
        "document": docs[c.document_id].title,
        "filename": docs[c.document_id].filename,
        "page": c.page_number,
        "score": round(float(s), 4),
    } for s, c in scored[:top_k]]


CHAT_SYSTEM = """You are the AI analyst inside the Senus PLC Board Report
platform, answering questions for board members, investors and credit
providers.

Rules:
- Answer ONLY from the provided source passages and validated metrics. If the
  answer isn't in them, say so plainly — never guess or use outside knowledge.
- Cite every factual claim as [document title, p.N].
- Money figures: state exactly as sourced, with EUR and the period.
- Be concise and board-appropriate: direct, factual, no hype.
- This is a pre-profit micro-cap: be honest about losses and risks; note the
  FY2028 EBITDA-positive guidance where relevant."""


def answer(db: Session, question: str, metrics_context: str) -> dict:
    from app.services.llm import complete, provider_available
    passages = retrieve(db, question)
    if not provider_available():
        return {"answer": ("AI chat requires an AI provider (set ANTHROPIC_API_KEY or "
                           "GITHUB_TOKEN). Retrieval still works - relevant passages are "
                           "shown below."),
                "citations": passages, "model": None}

    context = "\n\n".join(
        f"[{p['document']}, p.{p['page']}]\n{p['content']}" for p in passages)
    text, model_used = complete(
        CHAT_SYSTEM,
        f"Source passages:\n{context}\n\nValidated metrics:\n{metrics_context}"
        f"\n\nQuestion: {question}",
        max_tokens=1200)
    return {"answer": text, "citations": passages, "model": model_used}
