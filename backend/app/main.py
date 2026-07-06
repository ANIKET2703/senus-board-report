"""Senus Board Report API."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (auth, chat, documents, insights, metrics, scenario, statements,
                     validation, valuation)
from app.core.config import get_settings
from app.core.db import Base, engine

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Modern lifespan handler (replaces the deprecated @app.on_event hooks)."""
    Base.metadata.create_all(engine)
    # auto-seed on first boot so the app is demo-ready out of the box (fast: ~seconds)
    from pipeline.load import seed_database
    seed_database()
    # chunking the PDFs for retrieval is slow on small instances, so it runs in a
    # background thread: the port opens immediately and chat retrieval comes online
    # a few minutes later once chunks are stored
    import os
    if os.environ.get("SKIP_EMBED") != "1":
        import threading

        def _embed() -> None:
            from pipeline.embed import embed_documents
            try:
                embed_documents()
            except Exception as exc:  # chunking requires source PDFs; optional in prod image
                print(f"embed skipped: {exc}")

        threading.Thread(target=_embed, daemon=True).start()
    yield


app = FastAPI(
    title="Senus Board Report API",
    description="AI-native board reporting platform for Senus PLC (Assiduous Technology Graduate assignment)",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (auth.router, metrics.router, statements.router, insights.router,
               chat.router, documents.router, scenario.router, validation.router,
               valuation.router):
    app.include_router(router)


@app.get("/health")
def health():
    from app.services.llm import provider_available
    return {"status": "ok", "ai_provider": provider_available()}
