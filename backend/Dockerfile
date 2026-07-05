FROM python:3.12-slim

# poppler-utils: pdf2image page rendering for vision extraction
RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir \
    fastapi "uvicorn[standard]" sqlalchemy psycopg2-binary pydantic pydantic-settings \
    anthropic pdfplumber pdf2image "python-jose[cryptography]" bcrypt \
    python-multipart rank-bm25 openai

COPY backend/app ./app
COPY backend/pipeline ./pipeline
COPY data ../data

EXPOSE 8000
# bind to the platform-provided PORT when present (Render/Railway), else 8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
