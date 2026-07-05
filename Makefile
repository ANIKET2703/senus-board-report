.PHONY: dev test lint ingest seed up

up:            ## run full stack via docker compose
	docker compose up --build

dev-api:       ## run API locally (sqlite)
	cd backend && uvicorn app.main:app --reload

dev-web:       ## run frontend locally
	cd frontend && npm run dev

test:          ## backend test suite
	cd backend && python -m pytest tests/ -v

lint:
	cd backend && ruff check . || true
	cd frontend && npx eslint src --ext .ts,.tsx

ingest:        ## re-run AI extraction against source PDFs (needs ANTHROPIC_API_KEY)
	cd backend && python -m pipeline.run --extract

validate:      ## run accounting-identity checks on extracted facts
	cd backend && python -m pipeline.run --validate

seed:          ## seed database from validated facts
	cd backend && python -m pipeline.run --seed
