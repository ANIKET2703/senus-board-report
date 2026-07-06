# Senus Board Report - frontend

Next.js (App Router, TypeScript, Tailwind) client for the Senus PLC Board Report.
All data comes from the FastAPI backend; there are no hardcoded financial figures.

```bash
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev   # http://localhost:3000
```

Structure: `src/app` (login + dashboard routes), `src/components` (MetricCard,
InsightCard, ProvenanceTable, ApiDown), `src/lib` (typed API client, audience/
period/theme contexts, formatting). See the repository root README for the full
architecture, and `docs/ARCHITECTURE.md` for design decisions.
